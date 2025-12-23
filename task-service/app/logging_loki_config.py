import logging
import os
import logging_loki

SERVICE_NAME = os.getenv("SERVICE_NAME", "service")
LOKI_URL = os.getenv("LOKI_URL", "http://loki:3100/loki/api/v1/push")

def setup_logging():
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    loki_handler = logging_loki.LokiHandler(
        url=LOKI_URL,
        tags={"service": SERVICE_NAME},
        version="1",
    )
    loki_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    if not any(isinstance(h, logging_loki.LokiHandler) for h in root.handlers):
        root.addHandler(loki_handler)
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(console_handler)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        l = logging.getLogger(name)
        l.propagate = True
