from typing import List, Dict
from datetime import datetime
import httpx
import json
import time
import logging
from app.services.qdrant_service import qdrant_service
from app.services.embedding_service import embedding_service
from app.models.schemas import ComplianceCheckResponse, ViolationDetail, ComplianceCategory, TokenUsage

class ShariahComplianceAgent:
    def __init__(self, llm_api_url: str, llm_model_name: str):
        self.llm_api_url = llm_api_url
        self.llm_model_name = llm_model_name
        # Track token usage for each compliance check session
        self.session_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "process_time": 0.0}
    
    async def check_compliance(self, contract_id: str) -> ComplianceCheckResponse:
        # Reset token tracking for this compliance check
        self.session_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "process_time": 0.0}
        start_time = time.time()
        
        contract_chunks = qdrant_service.get_contract_chunks(contract_id)
        
        if not contract_chunks:
            raise ValueError(f"Contract {contract_id} not found")
        
        contract_text = "\n\n".join([chunk["text"] for chunk in sorted(contract_chunks, key=lambda x: x["chunk_index"])])
        filename = contract_chunks[0].get("filename", "Unknown Contract") if contract_chunks else "Unknown Contract"
        
        # Get all regulations for reference
        regulations = qdrant_service.get_all_regulations()
        
        if not regulations:
            raise ValueError("No Shariah regulations found in database")
        
        # Extract and analyze contract clauses for non-compliance
        violations = await self._analyze_contract_clauses(
            contract_text=contract_text,
            contract_chunks=contract_chunks,
            regulations=regulations
        )
        
        violations_count = len(violations)
        # Calculate compliance based on severity and number of violations
        compliance_percentage = self._calculate_compliance_score(violations)
        
        category = self._determine_category(compliance_percentage)
        
        summary = await self._generate_summary(
            compliance_percentage,
            violations_count,
            violations
        )
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            compliance_percentage,
            category,
            violations
        )
        
        # Calculate process time
        process_time = time.time() - start_time
        self.session_token_usage["process_time"] = process_time
        
        # Build response
        response = ComplianceCheckResponse(
            contract_id=contract_id,
            overall_score=round(compliance_percentage, 2),
            category=category,
            total_regulations_checked=len(regulations),
            compliant_count=0,  # Not applicable in clause-based analysis
            violations_count=violations_count,
            violations=violations,
            summary=summary,
            recommendations=recommendations,
            checked_at=datetime.utcnow(),
            token_usage=TokenUsage(
                prompt_tokens=self.session_token_usage["prompt_tokens"],
                completion_tokens=self.session_token_usage["completion_tokens"],
                total_tokens=self.session_token_usage["total_tokens"],
                process_time=self.session_token_usage["process_time"],
                timestamp=datetime.utcnow()
            )
        )
        
        # Save full compliance report to Qdrant for history
        try:
            # Prepare report dict for storage
            report_dict = response.dict()
            report_dict['filename'] = filename  # Add filename to stored report
            report_dict['checked_at'] = report_dict['checked_at'].isoformat()  # Convert datetime to string for JSON storage
            
            qdrant_service.update_contract_status(
                contract_id=contract_id,
                score=round(compliance_percentage, 2),
                category=category,
                status_summary=summary[:200] + "..." if len(summary) > 200 else summary,
                full_report=report_dict
            )
        except Exception as e:
            logging.error(f"Failed to update contract status history: {e}")
        
        return response
    
    async def _analyze_contract_clauses(
        self,
        contract_text: str,
        contract_chunks: List[Dict],
        regulations: List[Dict]
    ) -> List[ViolationDetail]:
        """Analyze contract clauses and identify non-compliant ones with regulation sources."""
        
        # Generate embedding for the contract text
        if len(contract_text) <= 2000:
            # Use full text if short
            contract_embedding = embedding_service.embed_text(contract_text)
        elif len(contract_text) <= 10000:
            # Chunk-based embedding for medium-length contracts
            chunk_size = 1000
            chunks = [contract_text[i:i + chunk_size] for i in range(0, len(contract_text), chunk_size)]
            chunk_embeddings = []
            for chunk in chunks:
                embedding = embedding_service.embed_text(chunk)
                chunk_embeddings.append(embedding)
            # Average the embeddings
            if chunk_embeddings:
                contract_embedding = [sum(values) / len(values) for values in zip(*chunk_embeddings)]
            else:
                contract_embedding = embedding_service.embed_text(contract_text[:2000])
        else:
            # Summarize long contracts and embed the summary
            summary = await self._summarize_contract(contract_text)
            contract_embedding = embedding_service.embed_text(summary)
        
        # Perform similarity search to get top relevant regulations
        relevant_regulations = qdrant_service.search_similar_regulations(
            query_embedding=contract_embedding,
            limit=10  # Top 10 most similar regulations
        )
        
        # Fallback to all regulations if search returns none
        if not relevant_regulations:
            relevant_regulations = regulations[:15]
        
        # Create a regulations context for the LLM
        regulations_context = "\n\n".join([
            f"[{reg.get('reference', 'REF-' + reg['id'][:8])}] {reg['title']}:\n{reg['content']}"
            for reg in relevant_regulations
        ])
        
        prompt = f"""As a qualified Shariah advisor, carefully review this contract for compliance with Islamic Shariah principles and identify ALL clauses that may contravene Shariah law.

SHARIAH REGULATIONS:
{regulations_context}

CONTRACT:
{contract_text[:5000]}

TASK: Identify EVERY clause or section in the contract that violates Shariah principles. For each violation:
1. Quote the exact problematic clause from the contract
2. Cite the specific regulation it violates (use the reference code)
3. Explain why it contravenes Shariah
4. Assess severity (high/medium/low)
5. Provide step-by-step reasoning for the decision

Respond ONLY with a JSON array in this exact format:
[
  {{
    "violated_clause": "exact quote from contract",
    "regulation_reference": "regulation reference code",
    "regulation_title": "regulation title",
    "description": "explanation of the violation",
    "severity": "high",
    "reasoning": "Step 1: ... Step 2: ... Conclusion: ..."
  }}
]

If NO violations found, return: []

Your JSON response:"""
        
        try:
            response = await self._call_llm(prompt)
            
            if not response or len(response.strip()) < 3:
                logging.warning("Empty LLM response for clause analysis")
                return []
            
            # Clean response to extract JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            violations_data = json.loads(response)
            
            if not isinstance(violations_data, list):
                logging.error(f"Expected list, got {type(violations_data)}")
                return []
            
            violations = []
            for item in violations_data:
                # Find which chunk contains this violated clause to get page numbers
                violated_clause = item.get('violated_clause', '')
                pages = self._find_pages_for_clause(violated_clause, contract_chunks)
                
                violations.append(ViolationDetail(
                    regulation_title=item.get('regulation_title', 'Unspecified Regulation'),
                    regulation_reference=item.get('regulation_reference', 'N/A'),
                    violated_clause=violated_clause if violated_clause else 'Not specified',
                    description=item.get('description', 'Violation detected'),
                    severity=item.get('severity', 'medium'),
                    pages=pages,
                    reasoning=item.get('reasoning', 'No reasoning provided')
                ))
            
            return violations
            
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error in clause analysis: {str(e)}, Response: {response[:500]}")
            return []
        except Exception as e:
            logging.error(f"Error analyzing contract clauses: {str(e)}")
            return []

    def _find_pages_for_clause(self, clause: str, contract_chunks: List[Dict]) -> List[int]:
        """Find which pages contain the given clause text."""
        if not clause or len(clause) < 10:
            return []
        
        pages = []
        # Search for the clause in chunks (using a substring match)
        clause_lower = clause.lower()[:100]  # Use first 100 chars for matching
        
        for chunk in contract_chunks:
            chunk_text = chunk.get("text", "").lower()
            chunk_pages = chunk.get("pages", [])
            
            # Check if clause appears in this chunk
            if clause_lower in chunk_text or chunk_text[:100] in clause_lower:
                pages.extend(chunk_pages)
        
        # Return unique sorted pages
        return sorted(list(set(pages)))
    
    def _calculate_compliance_score(self, violations: List[ViolationDetail]) -> float:
        """Calculate compliance score based on number and severity of violations."""
        if not violations:
            return 100.0
        
        # Deduct points based on severity
        total_deduction = 0
        for violation in violations:
            if violation.severity.lower() == 'high':
                total_deduction += 25
            elif violation.severity.lower() == 'medium':
                total_deduction += 15
            else:  # low
                total_deduction += 5
        
        # Calculate final score (minimum 0)
        score = max(0, 100 - total_deduction)
        return score
    
    async def _generate_summary(
        self,
        compliance_percentage: float,
        violations_count: int,
        violations: List[ViolationDetail]
    ) -> str:
        if violations_count == 0:
            return "The contract fully adheres to Shariah principles. No clauses were identified that contravene Islamic Shariah."
        
        high_severity = sum(1 for v in violations if v.severity.lower() == "high")
        medium_severity = sum(1 for v in violations if v.severity.lower() == "medium")
        low_severity = sum(1 for v in violations if v.severity.lower() == "low")
        
        summary = f"Compliance Score: {compliance_percentage:.1f}%. "
        summary += f"Analysis identified {violations_count} clause(s) that may contravene Shariah principles. "
        
        if high_severity > 0:
            summary += f"Critical: {high_severity} clause(s) with high-severity issues require immediate review and rectification. "
        if medium_severity > 0:
            summary += f"{medium_severity} clause(s) with medium-severity concerns identified. "
        if low_severity > 0:
            summary += f"{low_severity} clause(s) with low-severity issues noted. "
        
        summary += "Each issue includes the specific Shariah regulation source for reference."
        
        return summary
    
    def _determine_category(self, compliance_percentage: float) -> ComplianceCategory:
        if compliance_percentage >= 90:
            return ComplianceCategory.COMPLIANT
        elif compliance_percentage >= 60:
            return ComplianceCategory.PARTIALLY_COMPLIANT
        else:
            return ComplianceCategory.NON_COMPLIANT
    
    async def _generate_recommendations(
        self,
        compliance_percentage: float,
        category: ComplianceCategory,
        violations: List[ViolationDetail]
    ) -> List[str]:
        """Generate actionable recommendations based on compliance results using AI."""
        
        if not violations:
            prompt = f"""As a Shariah advisor, based on the compliance analysis showing {compliance_percentage:.1f}% adherence to Shariah principles and {category.value} status, 
            provide 3-4 concise recommendations for maintaining and enhancing Shariah compliance.
            Each recommendation should be 1-2 sentences, clear and practical. Focus on preventive measures and best practices aligned with Islamic principles."""
        else:
            violations_summary = "\n".join([f"- {v.description} (Severity: {v.severity})" for v in violations])
            prompt = f"""As a Shariah advisor, based on the compliance analysis showing {compliance_percentage:.1f}% adherence to Shariah principles and {category.value} status,
            with the following issues identified:
            {violations_summary}
            
            Provide 3-4 specific, actionable recommendations to address these concerns and improve Shariah compliance.
            Each recommendation should be 1-2 sentences, concise and practical. Prioritize based on severity and ensure alignment with Islamic Shariah."""
        
        response = await self._call_llm(prompt)
        
        # Parse the response into a list of recommendations
        recommendations = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line[0].isdigit() or line.startswith('•')):
                # Remove bullet points and clean up
                clean_line = line.lstrip('-•0123456789. ').strip()
                if clean_line:
                    recommendations.append(clean_line)
            elif line and len(recommendations) < 6:  # Fallback for non-bulleted responses
                recommendations.append(line)
        
        # Ensure we have at least some recommendations
        if not recommendations:
            recommendations = ["Consult with Shariah scholars for specific guidance", 
                             "Review contract terms against Islamic principles",
                             "Document all compliance considerations"]
        
        return recommendations[:6]  # Limit to 6 recommendations
    
    async def _summarize_contract(self, contract_text: str) -> str:
        """Summarize the contract text using the LLM for embedding purposes."""
        summary_prompt = f"""As a Shariah advisor, summarize the following contract in 500-1000 words, focusing on key terms, parties, obligations, and clauses that may impact Shariah compliance. Keep it concise but comprehensive:

{contract_text[:10000]}  # Limit input to prevent token overflow

Summary:"""
        
        summary = await self._call_llm(summary_prompt)
        return summary.strip()
    
    async def _call_llm(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "model": self.llm_model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 1500
                    }
                }
                
                response = await client.post(self.llm_api_url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                # Extract token usage information if available
                if "usage" in result:
                    usage = result["usage"]
                    self.session_token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                    self.session_token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
                    self.session_token_usage["total_tokens"] += usage.get("total_tokens", 0)
                elif "prompt_eval_count" in result:  # Ollama-specific format
                    self.session_token_usage["prompt_tokens"] += result.get("prompt_eval_count", 0)
                    self.session_token_usage["completion_tokens"] += result.get("eval_count", 0)
                    self.session_token_usage["total_tokens"] += (result.get("prompt_eval_count", 0) + result.get("eval_count", 0))
                
                # Extract content from response
                content = result.get("message", {}).get("content", "") or result.get("response", "")
                
                if not content or len(content.strip()) == 0:
                    logging.warning(f"Warning: Empty response from LLM. Prompt length: {len(prompt)}, Full response: {result}")
                    return '{"violation_found": false}'
                
                return content
        except httpx.TimeoutException:
            logging.error("LLM API timeout after 120s")
            return '{"violation_found": false}'
        except Exception as e:
            logging.error(f"LLM API error: {str(e)}")
            return '{"violation_found": false}'
