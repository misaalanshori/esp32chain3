# aop.py - Aspect-Oriented Programming (AOP) Decorators
import json
import time
from dto import ApiResponseDto

ROUTES = []

def route(path, method="GET"):
    """Aspect: Registers an MVC controller action to an HTTP path and method."""
    def decorator(fn):
        ROUTES.append((method.upper(), path, fn))
        return fn
    return decorator

def json_dto(dto_cls):
    """Aspect: Intercepts request body, parses into DTO, and injects as an argument."""
    def decorator(fn):
        async def wrapper(self, request, *args, **kwargs):
            try:
                raw_body = getattr(request, "body", b"")
                payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
                dto = dto_cls.from_dict(payload)
            except Exception as e:
                err_dto = ApiResponseDto(ok=False, error=f"Validation failed: {str(e)}")
                return 400, "application/json", json.dumps(err_dto.to_dict())
            return await fn(self, request, dto, *args, **kwargs)
        return wrapper
    return decorator

def timed(fn):
    """Aspect: Observability and execution timing."""
    async def wrapper(self, *args, **kwargs):
        t0 = time.ticks_us()
        res = await fn(self, *args, **kwargs)
        dt_us = time.ticks_diff(time.ticks_us(), t0)
        return res
    return wrapper

def handle_errors(fn):
    """Aspect: Global exception boundary wrapping controller actions."""
    async def wrapper(self, *args, **kwargs):
        try:
            return await fn(self, *args, **kwargs)
        except Exception as e:
            err_dto = ApiResponseDto(ok=False, error=str(e))
            return 500, "application/json", json.dumps(err_dto.to_dict())
    return wrapper
