import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# ✅ Ensure auth-service/ is importable
ROOT = Path(__file__).resolve().parents[1]  # auth-service/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # ✅ Force sqlite for tests
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'auth_test.db'}")
    monkeypatch.setenv("JWT_SECRET", "devsecret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("SERVICE_NAME", "auth-service-test")

    # ⚠️ IMPORTANT:
    # Don't reload models. Reloading declarative models re-defines tables -> InvalidRequestError.
    import app.config as config
    import importlib
    importlib.reload(config)

    import app.db as db
    importlib.reload(db)

    # Import models ONCE (no reload)
    import app.models as models

    # Create tables before app lifespan queries run
    models.Base.metadata.create_all(bind=db.engine)

    import app.main as main
    importlib.reload(main)

    with TestClient(main.app) as c:
        yield c
