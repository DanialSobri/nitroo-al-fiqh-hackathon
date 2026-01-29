"""Direct Ollama LLM client"""
import requests
from typing import Optional
import json
import pprint
import copy


class OllamaLLM:
    """LLM client that connects directly to Ollama"""
    
    def __init__(
        self,
        base_url: str,
        model: str = "phi4:14b"
    ):
        """
        Initialize Ollama LLM client
        
        Args:
            base_url: Base URL for Ollama (e.g., localhost:6443/)
            model: Model name to use (default: phi4:14b)
        """
        # Ensure base_url ends with /
        if not base_url.endswith('/'):
            base_url += '/'
        
        self.base_url = base_url
        self.chat_url = f"{base_url}api/chat"
        self.model = model
        
        # Test connection
        print(f"  Connecting to Ollama at: {self.base_url}")
        try:
            # Simple health check - try to list models
            health_url = f"{base_url}api/tags"
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print(f"  ✓ Connected to Ollama successfully")
            else:
                print(f"  ⚠ Ollama health check returned status {response.status_code}")
        except Exception as e:
            print(f"  ⚠ Could not verify Ollama connection: {e}")
            print(f"  Will attempt to use Ollama anyway")
    
    def invoke(self, prompt: str, max_retries: int = 2) -> str:
        """
        Invoke the LLM with a prompt
        
        Args:
            prompt: The prompt/question to send to the LLM
            max_retries: Maximum number of retry attempts for transient errors
            
        Returns:
            The LLM's response text
        """
        response_text, _ = self.invoke_with_metadata(prompt, max_retries)
        return response_text
    
    def invoke_with_metadata(self, prompt: str, max_retries: int = 2):
        """
        Invoke the LLM with a prompt and return both content and raw response
        
        Args:
            prompt: The prompt/question to send to the LLM
            max_retries: Maximum number of retry attempts for transient errors
            
        Returns:
            Tuple of (response_text, raw_response_dict)
        """
        # Retry logic for transient errors
        last_error = None
        for attempt in range(max_retries + 1):
            if attempt > 0:
                print(f"  Retry attempt {attempt}/{max_retries}...")
                import time
                time.sleep(2)  # Brief delay before retry
            
            # Prepare request
            headers = {
                'Content-Type': 'application/json',
            }
            
            # Prepare payload - Ollama API format
            # Split prompt into system message and user message if it contains system instructions
            # Check if prompt starts with system-like instructions
            if prompt.startswith("You are") or "CRITICAL" in prompt[:500] or "SOURCE DOCUMENTS" in prompt:
                # Extract system message (first part before SOURCE DOCUMENTS or Question)
                system_parts = []
                user_parts = []
                
                # Try to split at common markers
                if "SOURCE DOCUMENTS" in prompt or "SOURCE DOCUMENT" in prompt:
                    split_marker = "SOURCE DOCUMENTS" if "SOURCE DOCUMENTS" in prompt else "SOURCE DOCUMENT"
                    parts = prompt.split(split_marker, 1)
                    if len(parts) == 2:
                        system_parts.append(parts[0].strip())
                        user_parts.append(f"{split_marker}\n{parts[1].strip()}")
                    else:
                        # Fallback: use entire prompt as user message
                        user_parts.append(prompt)
                elif "Question:" in prompt or "Q:" in prompt:
                    # Split at Question marker
                    if "Question:" in prompt:
                        parts = prompt.split("Question:", 1)
                    else:
                        parts = prompt.split("Q:", 1)
                    if len(parts) == 2:
                        system_parts.append(parts[0].strip())
                        user_parts.append(f"Question: {parts[1].strip()}")
                    else:
                        user_parts.append(prompt)
                else:
                    # No clear split point, use entire prompt as user message
                    user_parts.append(prompt)
                
                # Build messages array
                messages = []
                if system_parts:
                    messages.append({
                        "role": "system",
                        "content": system_parts[0]
                    })
                messages.append({
                    "role": "user",
                    "content": user_parts[0] if user_parts else prompt
                })
            else:
                # Standard format - single user message
                messages = [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            
            # Check total prompt length (sum of all message contents)
            total_length = sum(len(msg.get("content", "")) for msg in messages)
            max_prompt_length = 32000  # Increased significantly - Ollama can handle large prompts
            
            # Never truncate if it contains SOURCE DOCUMENTS - that's critical context
            if total_length > max_prompt_length:
                if "SOURCE DOCUMENTS" in prompt or "SOURCE DOCUMENT" in prompt:
                    print(f"  ⚠ Warning: Prompt is {total_length} chars but contains SOURCE DOCUMENTS - keeping full prompt (may be slow)")
                else:
                    print(f"  ⚠ Warning: Prompt is {total_length} chars, truncating to {max_prompt_length}")
                    # Truncate the last user message only
                    if messages and len(messages) > 0:
                        last_msg = messages[-1]
                        if "content" in last_msg:
                            last_msg["content"] = last_msg["content"][:max_prompt_length] + "... [truncated]"
            
            try:
                # Debug: Log full request details
                print(f"\n{'='*80}")
                print(f"  📤 OLLAMA REQUEST DEBUG")
                print(f"{'='*80}")
                print(f"  URL: {self.chat_url}")
                print(f"  Method: POST")
                print(f"  Model: {self.model}")
                print(f"  Prompt length: {len(prompt)} characters")
                
                print(f"\n  📋 HEADERS:")
                pprint.pprint(headers, indent=4, width=100)
                
                # Show payload with truncated content if too long
                safe_payload = payload.copy()
                if 'messages' in safe_payload and len(safe_payload['messages']) > 0:
                    content = safe_payload['messages'][0].get('content', '')
                    if len(content) > 500:
                        safe_payload['messages'][0]['content'] = content[:500] + f"\n... [truncated, total length: {len(content)} chars]"
                
                print(f"\n  📦 PAYLOAD (Pretty Print):")
                pprint.pprint(safe_payload, indent=4, width=100)
                
                print(f"\n  📦 PAYLOAD (JSON):")
                print(json.dumps(payload, indent=2, ensure_ascii=False))
                print(f"{'='*80}\n")
                
                response = requests.post(
                    self.chat_url,
                    headers=headers,
                    json=payload,
                    timeout=120  # Increased timeout for LLM responses
                )
                
                # Debug: Log response details
                print(f"  📥 OLLAMA RESPONSE DEBUG")
                print(f"  Status Code: {response.status_code}")
                print(f"  Response Headers: {dict(response.headers)}")
                
                # Check response status
                if response.status_code != 200:
                    error_detail = f"HTTP {response.status_code}"
                    
                    try:
                        error_body = response.json()
                        print(f"\n  ❌ ERROR RESPONSE BODY:")
                        pprint.pprint(error_body, indent=4, width=100)
                        print(f"{'='*80}\n")
                        
                        if isinstance(error_body, dict):
                            if 'error' in error_body:
                                error_message = error_body['error']
                                error_detail = f"Ollama Error: {error_message}"
                            elif 'message' in error_body:
                                error_message = error_body['message']
                                error_detail = f"Ollama Error: {error_message}"
                            else:
                                error_detail = f"Ollama Error: {error_body}"
                    except:
                        error_text = response.text[:500]
                        error_detail += f": {error_text}"
                    
                    print(f"  ✗ Ollama error: {error_detail}")
                    
                    # Retry on 500 errors (might be transient)
                    if response.status_code == 500 and attempt < max_retries:
                        last_error = error_detail
                        print(f"  Server error detected, will retry...")
                        continue
                    
                    raise ValueError(f"Ollama returned error: {error_detail}")
                
                response.raise_for_status()
                result = response.json()
                
                # Log response structure for debugging
                print(f"  ✓ Received response (keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'})")
                
                # Show response but truncate very long content FOR DISPLAY ONLY
                # Use deepcopy to avoid modifying the original result
                safe_result = copy.deepcopy(result)
                if isinstance(safe_result, dict) and 'message' in safe_result:
                    msg = safe_result['message']
                    if isinstance(msg, dict) and 'content' in msg:
                        content = msg['content']
                        if len(content) > 500:
                            safe_result['message']['content'] = content[:500] + f"\n... [truncated, total length: {len(content)} chars]"
                
                print(f"\n  📥 SUCCESS RESPONSE BODY (Pretty Print):")
                pprint.pprint(safe_result, indent=4, width=100, depth=3)
                
                print(f"\n  📥 SUCCESS RESPONSE BODY (JSON):")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print(f"{'='*80}\n")
                
                # Extract message content from response
                # Ollama response format: {"message": {"role": "assistant", "content": "..."}, ...}
                content = None
                if isinstance(result, dict):
                    # Primary format: message.content (Ollama format)
                    if 'message' in result:
                        message_obj = result['message']
                        if isinstance(message_obj, dict):
                            content = message_obj.get('content')
                            if content and content.strip():
                                print(f"  ✓ Extracted content from message.content ({len(content)} chars)")
                        else:
                            # message is a string
                            content = str(message_obj)
                            if content and content.strip() != '{}':
                                pass
                            else:
                                content = None
                    
                    # Other possible formats
                    if not content:
                        if 'content' in result:
                            content = result['content']
                            if content and content.strip():
                                pass
                            else:
                                content = None
                    
                    if not content:
                        if 'text' in result:
                            content = result['text']
                            if content and content.strip():
                                pass
                            else:
                                content = None
                    
                    if not content:
                        if 'response' in result:
                            content = result['response']
                            if content and content.strip():
                                pass
                            else:
                                content = None
                    
                    # Log the full response for debugging if no content found
                    if not content:
                        print(f"  ⚠ Could not extract content from response. Keys: {list(result.keys())}")
                        print(f"  Full response preview: {str(result)[:500]}")
                        # Return the whole response as string if format is unknown
                        content = str(result)
                
                if not content:
                    content = str(result)
                
                # Return both content and raw response for token usage extraction
                return content, result
            
            except ValueError as e:
                # Re-raise immediately for non-retryable errors
                raise
            except requests.exceptions.Timeout:
                last_error = "Ollama request timed out. The LLM may be taking too long to respond."
                if attempt < max_retries:
                    continue
                raise ValueError(last_error)
            except requests.exceptions.RequestException as e:
                error_msg = f"Ollama request failed"
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_body = e.response.json()
                        if isinstance(error_body, dict):
                            if 'error' in error_body:
                                error_msg = f"Ollama Error: {error_body['error']}"
                            elif 'message' in error_body:
                                error_msg = f"Ollama Error: {error_body['message']}"
                            else:
                                error_msg += f": {error_body}"
                    except:
                        error_msg += f": {e.response.text[:500]}"
                else:
                    error_msg += f": {str(e)}"
                
                last_error = error_msg
                # Retry on 500 errors (might be transient)
                if attempt < max_retries and hasattr(e, 'response') and e.response and e.response.status_code == 500:
                    print(f"  Server error detected, will retry...")
                    continue
                raise ValueError(error_msg)
            except Exception as e:
                last_error = f"Failed to parse Ollama response: {e}"
                if attempt < max_retries:
                    continue
                raise ValueError(last_error)
        
        # If we get here, all retries failed
        raise ValueError(f"All retry attempts failed. Last error: {last_error}")


# Compatibility wrapper for LangChain-style interface
class OllamaChatLLM:
    """LangChain-compatible wrapper for Ollama LLM"""
    
    def __init__(self, ollama_llm: OllamaLLM):
        self.ollama_llm = ollama_llm
        self.last_response = None  # Store last raw response for token usage extraction
    
    def invoke(self, prompt: str):
        """Invoke method compatible with LangChain"""
        # Store raw response for token usage extraction
        response_text, raw_response = self.ollama_llm.invoke_with_metadata(prompt)
        self.last_response = raw_response
        
        # Return object with .content attribute like LangChain ChatOpenAI
        class Response:
            def __init__(self, content, response_metadata=None):
                self.content = content
                self.response_metadata = response_metadata or {}
        
        # Extract token usage from raw response
        metadata = {}
        if isinstance(raw_response, dict):
            if 'prompt_eval_count' in raw_response:
                metadata['prompt_eval_count'] = raw_response.get('prompt_eval_count')
                metadata['eval_count'] = raw_response.get('eval_count')
        
        return Response(response_text, metadata)
