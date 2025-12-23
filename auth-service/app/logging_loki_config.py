import logging
import os
import logging_loki

SERVICE_NAME = os.getenv("SERVICE_NAME", "service")
LOKI_URL = os.getenv("LOKI_URL", "http://loki:3100/loki/api/v1/push")

def setup_logging():
    handler = logging_loki.LokiHandler(
        url=LOKI_URL,
        tags={"service": SERVICE_NAME},
        version="1",
    )
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    # Also send uvicorn logs to root handlers
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        l = logging.getLogger(name)
        l.handlers = []          
        l.propagate = True      