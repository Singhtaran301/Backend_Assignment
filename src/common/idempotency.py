import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.common.cache import cache

class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. SKIP SAFE METHODS (GET, OPTIONS, HEAD)
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)

        # 2. CHECK HEADER
        idem_key = request.headers.get("Idempotency-Key")
        if not idem_key:
            return await call_next(request)

        # 3. GENERATE STORAGE KEY
        redis_key = f"idempotency:{request.url.path}:{idem_key}"

        # 4. CHECK CACHE (Hit)
        cached_response = await cache.get_cached_data(redis_key)
        if cached_response:
            return Response(
                content=cached_response["body"],
                status_code=cached_response["status_code"],
                media_type=cached_response["media_type"],
                headers={"X-Idempotency-Hit": "true"}
            )

        # 5. PROCESS REQUEST (Miss)
        response = await call_next(request)

        # 6. CACHE RESPONSE (Only if success)
        if response.status_code < 500:
            # --- ROBUST BODY READING (Fixes Test Error) ---
            response_body_bytes = b""

            # Check if the iterator is Async (Real Server) or Sync (Test Client)
            if hasattr(response.body_iterator, "__aiter__"):
                async for chunk in response.body_iterator:
                    response_body_bytes += chunk
            else:
                for chunk in response.body_iterator:
                    response_body_bytes += chunk

            # Store decoded string for Redis JSON
            body_str = response_body_bytes.decode()

            # IMPORTANT: We consumed the stream. We must "rewind" it 
            # so the client/server can read it again. 
            # We wrap it in an async generator because Starlette expects that.
            async def re_iterator():
                yield response_body_bytes
            
            response.body_iterator = re_iterator()

            data_to_cache = {
                "status_code": response.status_code,
                "body": body_str,
                "media_type": response.media_type
            }
            
            # TTL: 24 Hours
            await cache.set_cached_data(redis_key, data_to_cache)
            await cache.redis.expire(redis_key, 60 * 60 * 24)

        return response