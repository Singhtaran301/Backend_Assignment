import json
import hashlib
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.common.cache import cache

class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. SKIP SAFE METHODS (GET, OPTIONS, HEAD)
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)

        # 2. CHECK HEADER
        # The client MUST send this header for critical writes.
        # Format: "Idempotency-Key: <UUID>"
        idem_key = request.headers.get("Idempotency-Key")

        if not idem_key:
            # OPTIONAL: You can enforce strictness here.
            # For now, we allow requests without keys to avoid breaking Auth/Admin.
            # If you want strict mode, uncomment the lines below:
            # return JSONResponse(
            #     status_code=400, 
            #     content={"detail": "Missing Idempotency-Key header"}
            # )
            return await call_next(request)

        # 3. GENERATE STORAGE KEY
        # We combine User ID (if available) + Key to prevent collisions
        # But middleware runs before Auth, so we rely on the Key + Path.
        # Structure: "idempotency:<path>:<key>"
        redis_key = f"idempotency:{request.url.path}:{idem_key}"

        # 4. CHECK CACHE (Hit)
        cached_response = await cache.get_cached_data(redis_key)
        if cached_response:
            print(f"🛡️ Idempotency Hit! Replaying response for {idem_key}")
            return Response(
                content=cached_response["body"],
                status_code=cached_response["status_code"],
                media_type=cached_response["media_type"],
                headers={"X-Idempotency-Hit": "true"}
            )

        # 5. PROCESS REQUEST (Miss)
        response = await call_next(request)

        # 6. CACHE RESPONSE (Only if success)
        # We only cache 2xx and 4xx. We don't cache 500s (server errors should be retried).
        if response.status_code < 500:
            response_body = [section async for section in response.body_iterator]
            response.body_iterator = iter(response_body) # Reset iterator so client can read it
            body_content = b"".join(response_body).decode()

            data_to_cache = {
                "status_code": response.status_code,
                "body": body_content,
                "media_type": response.media_type
            }
            
            # TTL: 24 Hours (Standard practice)
            await cache.set_cached_data(redis_key, data_to_cache)
            # Override TTL to 24 hours (default cache is 60s)
            await cache.redis.expire(redis_key, 60 * 60 * 24)

        return response