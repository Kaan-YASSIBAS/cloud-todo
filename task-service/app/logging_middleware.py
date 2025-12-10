import logging
import time
from fastapi import FastAPI, Request
from .config import settings

logger = logging.getLogger(settings.SERVICE_NAME)
logger.setLevel(logging.INFO)

async def _log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    dur_ms = int((time.time() - start) * 1000)
    logger.info(
        f"path={request.url.path} method={request.method} "
        f"status={response.status_code} dur={dur_ms}ms"
    )
    return response

def setup_logging(app: FastAPI) -> None:
    app.middleware("http")(_log_requests)

