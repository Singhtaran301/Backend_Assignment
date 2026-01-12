import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from src.core.logger import setup_logger

logger = setup_logger("middleware")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Generate Request ID (Trace Context)
        request_id = str(uuid.uuid4())
        
        # 2. Add to Logger Context (So all logs know this ID)
        # Note: In a real production app, use contextvars for thread safety.
        # For this assignment, we pass it via headers/logs manually if needed.
        
        # 3. Time the Request (Latency Metric)
        start_time = time.time()
        
        # 4. Process Request
        response = await call_next(request)
        
        # 5. Calculate Duration
        process_time = time.time() - start_time
        
        # 6. Log Structured JSON
        # No PII (Don't log email/password bodies)
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": round(process_time, 4),
            "request_id": request_id
        }
        
        # Log 500s as Errors, 200s as Info
        if response.status_code >= 500:
            logger.error("Request Failed", extra=log_data)
        else:
            logger.info("Request Completed", extra=log_data)
            
        # 7. Propagate Request ID to Client (Correlation)
        response.headers["X-Request-ID"] = request_id
        
        return response