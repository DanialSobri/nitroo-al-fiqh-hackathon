from typing import List, Dict
from datetime import datetime
import httpx
import json
from app.services.qdrant_service import qdrant_service
from app.services.embedding_service import embedding_service
from app.models.schemas import ComplianceCheckResponse, ViolationDetail, ComplianceCategory

class ShariahComplianceAgent:
    def __init__(self, llm_api_url: str, llm_model_name: str):
        self.llm_api_url = llm_api_url
        self.llm_model_name = llm_model_name
    
    async def check_compliance(self, contract_id: str) -> ComplianceCheckResponse:
        contract_chunks = qdrant_service.get_contract_chunks(contract_id)
        
        if not contract_chunks:
            raise ValueError(f"Contract {contract_id} not found")
        
        contract_text = "\n\n".join([chunk["text"] for chunk in sorted(contract_chunks, key=lambda x: x["chunk_index"])])
        filename = contract_chunks[0].get("filename", "Unknown Contract") if contract_chunks else "Unknown Contract"
        
        # First, generate a comprehensive summary of the contract to better understand its content
        contract_summary = await self._summarize_contract(contract_text)
        
        regulations = qdrant_service.get_all_regulations()
        
        if not regulations:
            raise ValueError("No Shariah regulations found in database")
        
        violations = []
        compliant_count = 0
        
        for regulation in regulations:
            violation = await self._analyze_regulation_compliance(
                contract_text=contract_text,
                contract_summary=contract_summary,
                regulation=regulation
            )
            
            if violation:
                violations.append(violation)
            else:
                compliant_count += 1
        
        total_regulations = len(regulations)
        violations_count = len(violations)
        compliance_percentage = (compliant_count / total_regulations * 100) if total_regulations > 0 else 0
        
        category = self._determine_category(compliance_percentage)
        
        summary = await self._generate_summary(
            compliance_percentage,
            total_regulations,
            compliant_count,
            violations_count,
            violations
        )
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            compliance_percentage,
            category,
            violations
        )
        
        # Build response
        response = ComplianceCheckResponse(
            contract_id=contract_id,
            overall_score=round(compliance_percentage, 2),
            category=category,
            total_regulations_checked=total_regulations,
            compliant_count=compliant_count,
            violations_count=violations_count,
            violations=violations,
            summary=summary,
            recommendations=recommendations,
            checked_at=datetime.utcnow()
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
            print(f"Failed to update contract status history: {e}")
        
        return response
    
    async def _summarize_contract(self, contract_text: str) -> str:
        """Generate a detailed summary of the contract to aid in compliance analysis."""
        prompt = f"""Summarize this contract focusing on financial terms, interest rates, fees, and payment structures.

Contract:
{contract_text[:3000]}

Summary:"""

        try:
            response = await self._call_llm(prompt)
            if response and len(response) > 50:
                return response
            else:
                print(f"Contract summary too short or empty, using text excerpt instead")
                return contract_text[:2000]
        except Exception as e:
            print(f"Failed to summarize contract: {e}")
            return contract_text[:2000]

    async def _analyze_regulation_compliance(
        self,
        contract_text: str,
        contract_summary: str,
        regulation: Dict
    ) -> ViolationDetail | None:
        prompt = f"""Analyze if this contract violates the Shariah regulation below.

REGULATION:
{regulation['title']}
{regulation['content']}

CONTRACT EXCERPT:
{contract_text[:4000]}

TASK: Check if the contract violates this regulation. Look for:
- Interest rates, APR, finance charges (for riba regulations)
- Uncertain terms or hidden conditions (for gharar regulations)
- Prohibited activities (for haram regulations)

Respond ONLY with JSON in this exact format:

If violation found:
{{"violation_found": true, "violated_section": "quote from contract", "description": "explain the violation", "severity": "high"}}

If no violation:
{{"violation_found": false}}

Your JSON response:"""

        try:
            response = await self._call_llm(prompt)
            
            if not response or len(response) < 10:
                print(f"Empty or invalid LLM response for {regulation['title']}")
                return None
            
            # Clean response to extract JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            result = json.loads(response)
            
            if result.get("violation_found"):
                return ViolationDetail(
                    regulation_title=regulation['title'],
                    regulation_reference=regulation.get('reference'),
                    violated_section=result.get('violated_section', 'Not specified'),
                    description=result.get('description', 'Violation detected'),
                    severity=result.get('severity', 'high')
                )
        except json.JSONDecodeError as e:
            print(f"JSON parsing error for {regulation['title']}: {str(e)}, Response: {response[:500]}")
        except Exception as e:
            print(f"Error analyzing regulation {regulation['title']}: {str(e)}")
        
        return None
    
    async def _generate_summary(
        self,
        compliance_percentage: float,
        total_regulations: int,
        compliant_count: int,
        violations_count: int,
        violations: List[ViolationDetail]
    ) -> str:
        if violations_count == 0:
            return f"The contract is fully Shariah compliant. All {total_regulations} regulations were checked and no violations were found."
        
        high_severity = sum(1 for v in violations if v.severity == "high")
        medium_severity = sum(1 for v in violations if v.severity == "medium")
        low_severity = sum(1 for v in violations if v.severity == "low")
        
        summary = f"Compliance Score: {compliance_percentage:.1f}%. "
        summary += f"Out of {total_regulations} regulations checked, {compliant_count} were compliant and {violations_count} violations were found. "
        
        if high_severity > 0:
            summary += f"Critical: {high_severity} high-severity violations require immediate attention. "
        if medium_severity > 0:
            summary += f"{medium_severity} medium-severity issues identified. "
        if low_severity > 0:
            summary += f"{low_severity} low-severity concerns noted. "
        
        summary += "Review the detailed violations list for specific corrections needed."
        
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
        """Generate actionable recommendations based on compliance results."""
        
        recommendations = []
        
        if category == ComplianceCategory.COMPLIANT:
            recommendations.append("✓ Contract is Shariah-compliant and ready for execution")
            recommendations.append("Maintain regular reviews to ensure ongoing compliance with Islamic principles")
            recommendations.append("Keep documentation for audit and governance purposes")
        elif category == ComplianceCategory.NON_COMPLIANT:
            recommendations.append("⚠️ URGENT: Do not proceed with this contract in its current form")
            recommendations.append("Consult with a qualified Shariah scholar or Islamic finance expert immediately")
            recommendations.append("Major restructuring required to align with Islamic principles")
            
            # Add specific recommendations based on violations
            if violations:
                critical_issues = [v for v in violations if v.severity.lower() in ['high', 'critical']]
                if critical_issues:
                    recommendations.append(f"Priority: Address {len(critical_issues)} critical violation(s) first")
                
                # Check for common issues
                violation_texts = " ".join([v.description.lower() for v in violations])
                if 'riba' in violation_texts or 'interest' in violation_texts:
                    recommendations.append("Replace interest-based terms with profit-sharing (Mudarabah) or cost-plus (Murabaha) structures")
                if 'gharar' in violation_texts or 'uncertainty' in violation_texts:
                    recommendations.append("Remove ambiguous terms and clearly define all contract obligations")
                if 'gambling' in violation_texts or 'maysir' in violation_texts:
                    recommendations.append("Eliminate speculative elements and ensure transactions are asset-backed")
        else:  # PARTIALLY_COMPLIANT
            recommendations.append("⚠️ Contract requires modifications before proceeding")
            recommendations.append("Review and address identified violations with legal and Shariah advisors")
            recommendations.append("Consider gradual remediation starting with high-severity issues")
            
            if violations:
                high_sev = len([v for v in violations if v.severity.lower() == 'high'])
                if high_sev > 0:
                    recommendations.append(f"Focus on resolving {high_sev} high-severity violation(s) as priority")
        
        return recommendations
    
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
                        "num_predict": 500
                    }
                }
                
                response = await client.post(self.llm_api_url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                # Extract content from response
                content = result.get("message", {}).get("content", "") or result.get("response", "")
                
                if not content or len(content.strip()) == 0:
                    print(f"Warning: Empty response from LLM. Prompt length: {len(prompt)}, Full response: {result}")
                    return '{"violation_found": false}'
                
                return content
        except httpx.TimeoutException:
            print(f"LLM API timeout after 120s")
            return '{"violation_found": false}'
        except Exception as e:
            print(f"LLM API error: {str(e)}")
            return '{"violation_found": false}'
