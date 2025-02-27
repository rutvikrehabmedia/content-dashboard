from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid
import json
import os
import logging
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, log_dir="logs"):
        super().__init__(app)
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extract basic request info
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Create log entry with basic info
        log_entry = {
            "id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "method": method,
            "path": path,
            "ip": client_host,
            "user_agent": user_agent,
        }
        
        # Capture request body only for non-GET requests and if not a file upload
        request_body = None
        if method != "GET" and not path.startswith("/api/upload"):
            try:
                # Clone the request to read the body
                body_bytes = await request.body()
                request_body = body_bytes.decode()
                # Restore the request body
                request._body = body_bytes
                
                # Try to parse as JSON
                try:
                    request_body = json.loads(request_body)
                except:
                    pass
            except Exception as e:
                logger.error(f"Error reading request body: {str(e)}")
        
        # Store request details
        log_entry["request"] = {
            "headers": dict(request.headers),
            "query_params": query_params,
            "body": request_body
        }
        
        # Set default level
        log_entry["level"] = "info"
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            log_entry["duration_ms"] = round(duration * 1000, 2)
            
            # Get response status
            status_code = response.status_code
            log_entry["status_code"] = status_code
            
            # Set log level based on status code
            if status_code >= 500:
                log_entry["level"] = "error"
            elif status_code >= 400:
                log_entry["level"] = "warning"
            
            # Capture response body for API endpoints
            if path.startswith("/api/") and path != "/api/logs":  # Skip logging responses from the logs API
                try:
                    # Get the original response body
                    response_body = [section async for section in response.body_iterator]
                    response.body_iterator = iter(response_body)
                    
                    # Decode and parse the response body
                    body_text = b"".join(response_body).decode()
                    try:
                        body_json = json.loads(body_text)
                        # For large responses, only store a summary
                        if len(body_text) > 10000:  # If response is larger than ~10KB
                            if isinstance(body_json, list):
                                body_json = {
                                    "summary": f"List with {len(body_json)} items",
                                    "first_few_items": body_json[:3] if len(body_json) > 0 else []
                                }
                            elif isinstance(body_json, dict):
                                # Keep only the first level keys and their types
                                body_json = {
                                    "summary": "Large dictionary response",
                                    "keys": {k: str(type(v).__name__) for k, v in body_json.items()}
                                }
                    except:
                        # If not JSON, truncate large text responses
                        if len(body_text) > 1000:
                            body_text = body_text[:1000] + "... [truncated]"
                    
                    log_entry["response"] = {
                        "headers": dict(response.headers),
                        "body": body_json if "body_json" in locals() else body_text
                    }
                except Exception as e:
                    logger.error(f"Error capturing response body: {str(e)}")
                    log_entry["response"] = {
                        "headers": dict(response.headers),
                        "body": "[Error capturing response body]"
                    }
            else:
                # For non-API endpoints or logs API, just log headers
                log_entry["response"] = {
                    "headers": dict(response.headers),
                    "body": "[Response body not logged]"
                }
            
            # Add message
            log_entry["message"] = f"{method} {path} - {status_code}"
            
            return response
            
        except Exception as e:
            # Log exceptions
            duration = time.time() - start_time
            log_entry["duration_ms"] = round(duration * 1000, 2)
            log_entry["level"] = "error"
            log_entry["status_code"] = 500
            log_entry["error"] = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            }
            log_entry["message"] = f"Error processing {method} {path}: {str(e)}"
            
            # Re-raise the exception
            raise
            
        finally:
            # Write log to file
            try:
                log_file = os.path.join(self.log_dir, f"{request_id}.json")
                with open(log_file, "w") as f:
                    json.dump(log_entry, f, indent=2)
            except Exception as e:
                logger.error(f"Error writing log file: {str(e)}") 