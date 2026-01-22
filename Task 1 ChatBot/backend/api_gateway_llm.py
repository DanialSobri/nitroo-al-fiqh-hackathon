"""API Gateway LLM client for Ollama via API Gateway"""
import requests
from typing import Optional, List, Dict, Any
import time
import json
import pprint
import copy


class APIGatewayLLM:
    """LLM client that uses API Gateway to access Ollama"""
    
    def __init__(
        self,
        token_url: str,
        chat_url: str,
        auth_header: str,
        model: str = "phi4:14b",
        cookie: Optional[str] = None
    ):
        """
        Initialize API Gateway LLM client
        
        Args:
            token_url: URL to get authentication token
            chat_url: URL for chat API endpoint
            auth_header: Basic auth header (Authorization: Basic ...)
            model: Model name to use (default: phi4:14b)
            cookie: Optional cookie string for requests
        """
        self.token_url = token_url
        self.chat_url = chat_url
        self.auth_header = auth_header
        self.model = model
        self.cookie = cookie
        self._token: Optional[str] = None
        self._token_expiry: float = 0
        
        # Pre-fetch token during initialization
        print("  Fetching API Gateway token...")
        try:
            self._get_token()
            print("  ✓ Token obtained successfully")
        except Exception as e:
            print(f"  ⚠ Warning: Could not fetch token during initialization: {e}")
            print("  Token will be fetched on first LLM call")
    
    def _get_token(self) -> str:
        """Get or refresh authentication token - MUST be called before LLM API calls"""
        # Check if token is still valid (with 5 minute buffer)
        if self._token and time.time() < self._token_expiry - 300:
            return self._token
        
        # Request new token - this MUST happen before any LLM API call
        print("  Requesting new API Gateway token...")
        headers = {
            'Authorization': self.auth_header,
        }
        if self.cookie:
            headers['Cookie'] = self.cookie
        
        try:
            # Make sure to call the token endpoint first
            token_endpoint = f"{self.token_url}?grant_type=client_credentials&scope=chat"
            
            # Debug: Log token request
            print(f"\n{'='*80}")
            print(f"  🔑 TOKEN REQUEST DEBUG")
            print(f"{'='*80}")
            print(f"  URL: {token_endpoint}")
            print(f"  Method: POST")
            safe_headers = headers.copy()
            if 'Authorization' in safe_headers:
                auth_val = safe_headers['Authorization']
                safe_headers['Authorization'] = f"{auth_val[:30]}... [masked]" if len(auth_val) > 30 else "[masked]"
            print(f"  Headers:")
            pprint.pprint(safe_headers, indent=4, width=100)
            print(f"{'='*80}\n")
            
            response = requests.post(
                token_endpoint,
                headers=headers,
                timeout=10
            )
            
            # Debug: Log token response
            print(f"  🔑 TOKEN RESPONSE DEBUG")
            print(f"  Status Code: {response.status_code}")
            print(f"  Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            token_data = response.json()
            
            # Mask token in debug output
            safe_token_data = token_data.copy()
            if 'access_token' in safe_token_data:
                token_val = safe_token_data['access_token']
                safe_token_data['access_token'] = f"{token_val[:30]}... [masked]" if len(token_val) > 30 else "[masked]"
            
            print(f"  Response Body:")
            pprint.pprint(safe_token_data, indent=4, width=100)
            print(f"{'='*80}\n")
            
            self._token = token_data.get('access_token')
            
            # Set expiry (default to 1 hour if not provided)
            expires_in = token_data.get('expires_in', 3600)
            self._token_expiry = time.time() + expires_in
            
            if not self._token:
                raise ValueError("No access_token in response")
            
            print(f"  ✓ Token obtained (expires in {expires_in}s)")
            return self._token
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to get API Gateway token: HTTP {e.response.status_code if hasattr(e, 'response') else 'N/A'}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {e.response.text[:200]}"
            raise ValueError(error_msg)
        except Exception as e:
            raise ValueError(f"Failed to get API Gateway token: {e}")
    
    def invoke(self, prompt: str, max_retries: int = 2) -> str:
        """
        Invoke the LLM with a prompt
        
        Args:
            prompt: The prompt/question to send to the LLM
            max_retries: Maximum number of retry attempts for transient errors
            
        Returns:
            The LLM's response text
        """
        # CRITICAL: Get token FIRST before making any LLM API call
        # This ensures we always have a valid token before calling the chat API
        token = self._get_token()
        
        if not token:
            raise ValueError("No valid token available. Cannot call LLM API.")
        
        # Retry logic for transient errors
        last_error = None
        for attempt in range(max_retries + 1):
            if attempt > 0:
                print(f"  Retry attempt {attempt}/{max_retries}...")
                # Refresh token on retry
                token = self._get_token()
                time.sleep(2)  # Brief delay before retry
            
            # Prepare request
            headers = {
                'accept': '*/*',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
            }
            if self.cookie:
                headers['Cookie'] = self.cookie
            
            # Prepare payload - ensure it matches API Gateway expected format
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False
            }
            
            # If prompt is very long, truncate it (some APIs have limits)
            # Reduced limit to ensure smaller payloads
            max_prompt_length = 5000  # Reduced from 8000 for smaller payloads
            if len(prompt) > max_prompt_length:
                print(f"  ⚠ Warning: Prompt is {len(prompt)} chars, truncating to {max_prompt_length}")
                payload["messages"][0]["content"] = prompt[:max_prompt_length] + "... [truncated]"
            
            try:
                # Debug: Log full request details
                print(f"\n{'='*80}")
                print(f"  📤 API GATEWAY CHAT REQUEST DEBUG")
                print(f"{'='*80}")
                print(f"  URL: {self.chat_url}")
                print(f"  Method: POST")
                print(f"  Model: {self.model}")
                print(f"  Prompt length: {len(prompt)} characters")
                
                # Mask sensitive data in headers
                safe_headers = headers.copy()
                if 'Authorization' in safe_headers:
                    auth_val = safe_headers['Authorization']
                    if len(auth_val) > 30:
                        safe_headers['Authorization'] = f"{auth_val[:30]}... [masked]"
                if 'Cookie' in safe_headers:
                    cookie_val = safe_headers['Cookie']
                    if len(cookie_val) > 50:
                        safe_headers['Cookie'] = f"{cookie_val[:50]}... [masked]"
                
                print(f"\n  📋 HEADERS:")
                pprint.pprint(safe_headers, indent=4, width=100)
                
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
                print(f"  📥 API GATEWAY CHAT RESPONSE DEBUG")
                print(f"  Status Code: {response.status_code}")
                print(f"  Response Headers: {dict(response.headers)}")
                
                # Check response status
                if response.status_code != 200:
                    error_detail = f"HTTP {response.status_code}"
                    is_tenant_error = False
                    error_message = None
                    
                    try:
                        error_body = response.json()
                        print(f"\n  ❌ ERROR RESPONSE BODY:")
                        pprint.pprint(error_body, indent=4, width=100)
                        print(f"{'='*80}\n")
                        
                        # Handle JSON error responses (not SOAP)
                        if isinstance(error_body, dict):
                            # Check for various error formats
                            if 'Fault' in error_body:
                                # Legacy SOAP-like format in JSON
                                fault = error_body['Fault']
                                error_message = fault.get('faultstring', fault.get('message', 'Unknown error'))
                                fault_code = fault.get('faultcode', 'Unknown')
                                error_detail = f"API Gateway Error ({fault_code}): {error_message}"
                            elif 'error' in error_body:
                                # Standard error format
                                error_obj = error_body['error']
                                if isinstance(error_obj, dict):
                                    error_message = error_obj.get('message', error_obj.get('description', str(error_obj)))
                                    error_code = error_obj.get('code', 'Unknown')
                                    error_detail = f"API Gateway Error ({error_code}): {error_message}"
                                else:
                                    error_message = str(error_obj)
                                    error_detail = f"API Gateway Error: {error_message}"
                            elif 'message' in error_body:
                                error_message = error_body['message']
                                error_detail = f"API Gateway Error: {error_message}"
                            elif 'errorMessage' in error_body:
                                error_message = error_body['errorMessage']
                                error_detail = f"API Gateway Error: {error_message}"
                            elif 'description' in error_body:
                                error_message = error_body['description']
                                error_detail = f"API Gateway Error: {error_message}"
                            else:
                                # Unknown format, include full response
                                error_detail = f"API Gateway Error: {error_body}"
                                error_message = str(error_body)
                            
                            # Check for tenant activation errors
                            if error_message and 'tenant activation' in error_message.lower():
                                is_tenant_error = True
                                error_detail += "\n\nThis is a tenant activation issue with the API Gateway. This is NOT a transient error and cannot be retried.\nPlease verify:\n- API Gateway tenant is properly activated\n- Authentication credentials are correct\n- Service subscription is active\n- Contact API Gateway administrator"
                                # Don't retry tenant activation errors
                                raise ValueError(error_detail)
                            elif error_message and ('authentication' in error_message.lower() or 'authorization' in error_message.lower()):
                                error_detail += "\n\nAuthentication/Authorization issue. Please check:\n- API Gateway auth header is correct\n- Token is valid\n- Service permissions are correct"
                        else:
                            error_detail += f": {error_body}"
                            error_message = str(error_body)
                    except ValueError:
                        # Re-raise tenant activation errors immediately
                        raise
                    except Exception as e:
                        # If JSON parsing fails, try text
                        error_text = response.text[:500]
                        error_detail += f": {error_text}"
                        error_message = error_text
                        print(f"  Could not parse error as JSON: {e}")
                    
                    print(f"  ✗ API Gateway error: {error_detail}")
                    
                    # Don't retry on certain errors (tenant activation, auth issues)
                    if is_tenant_error or (error_message and 'tenant activation' in error_message.lower()):
                        raise ValueError(error_detail)
                    
                    # Retry on 500 errors (might be transient)
                    if response.status_code == 500 and attempt < max_retries:
                        last_error = error_detail
                        print(f"  Server error detected, will retry...")
                        continue
                    
                    raise ValueError(f"API Gateway returned error: {error_detail}")
                
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
                # API Gateway/Ollama response format: {"message": {"role": "assistant", "content": "..."}, ...}
                if isinstance(result, dict):
                    # Primary format: message.content (Ollama/API Gateway format)
                    if 'message' in result:
                        message_obj = result['message']
                        if isinstance(message_obj, dict):
                            content = message_obj.get('content')
                            if content and content.strip():
                                print(f"  ✓ Extracted content from message.content ({len(content)} chars)")
                                return content
                        else:
                            # message is a string
                            content = str(message_obj)
                            if content and content.strip() != '{}':
                                return content
                    
                    # OpenAI-compatible format: choices[0].message.content
                    if 'choices' in result and len(result['choices']) > 0:
                        message = result['choices'][0].get('message', {})
                        content = message.get('content', '')
                        if content and content.strip():
                            print(f"  ✓ Extracted content from choices[0].message.content")
                            return content
                    
                    # Other possible formats
                    if 'content' in result:
                        content = result['content']
                        if content and content.strip():
                            return content
                    
                    if 'text' in result:
                        content = result['text']
                        if content and content.strip():
                            return content
                    
                    if 'response' in result:
                        content = result['response']
                        if content and content.strip():
                            return content
                    
                    if 'answer' in result:
                        content = result['answer']
                        if content and content.strip():
                            return content
                    
                    # Log the full response for debugging if no content found
                    print(f"  ⚠ Could not extract content from response. Keys: {list(result.keys())}")
                    print(f"  Full response preview: {str(result)[:500]}")
                    # Return the whole response as string if format is unknown
                    return str(result)
                else:
                    return str(result)
            
            except ValueError as e:
                # Re-raise immediately for non-retryable errors (like tenant activation)
                raise
            except requests.exceptions.Timeout:
                last_error = "API Gateway request timed out. The LLM may be taking too long to respond."
                if attempt < max_retries:
                    continue
                raise ValueError(last_error)
            except requests.exceptions.RequestException as e:
                error_msg = f"API Gateway request failed"
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_body = e.response.json()
                        # Handle JSON error responses
                        if isinstance(error_body, dict):
                            if 'Fault' in error_body:
                                # Legacy format
                                fault = error_body['Fault']
                                fault_string = fault.get('faultstring', fault.get('message', 'Unknown error'))
                                error_msg = f"API Gateway Error: {fault_string}"
                            elif 'error' in error_body:
                                error_obj = error_body['error']
                                if isinstance(error_obj, dict):
                                    error_msg = f"API Gateway Error: {error_obj.get('message', error_obj.get('description', str(error_obj)))}"
                                else:
                                    error_msg = f"API Gateway Error: {error_obj}"
                            elif 'message' in error_body:
                                error_msg = f"API Gateway Error: {error_body['message']}"
                            else:
                                error_msg += f": {error_body}"
                            
                            # Check for tenant activation errors
                            error_text = str(error_body).lower()
                            if 'tenant activation' in error_text:
                                raise ValueError(error_msg)
                        else:
                            error_msg += f": {error_body}"
                    except ValueError:
                        raise
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
                last_error = f"Failed to parse API Gateway response: {e}"
                if attempt < max_retries:
                    continue
                raise ValueError(last_error)
        
        # If we get here, all retries failed
        raise ValueError(f"All retry attempts failed. Last error: {last_error}")


# Compatibility wrapper for LangChain-style interface
class APIGatewayChatLLM:
    """LangChain-compatible wrapper for API Gateway LLM"""
    
    def __init__(self, api_gateway_llm: APIGatewayLLM):
        self.api_gateway_llm = api_gateway_llm
    
    def invoke(self, prompt: str) -> Any:
        """Invoke method compatible with LangChain"""
        response_text = self.api_gateway_llm.invoke(prompt)
        
        # Return object with .content attribute like LangChain ChatOpenAI
        class Response:
            def __init__(self, content):
                self.content = content
        
        return Response(response_text)
