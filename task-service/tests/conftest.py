import sys
from pathlib import Path
import pytest
import jwt
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]  # task-service/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def token(monkeypatch):
    # require_auth genelde JWT_SECRET/JWT_ALGORITHM ile verify eder
    secret = "devsecret"
    alg = "HS256"
    # çoğu projede kullanıcı "sub" claim’inde olur
    return jwt.encode({"sub": "testuser"}, secret, algorithm=alg)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'task_test.db'}")
    monkeypatch.setenv("JWT_SECRET", "devsecret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("SERVICE_NAME", "task-service-test")

    import importlib
    import app.config as config
    importlib.reload(config)

    import app.db as db
    importlib.reload(db)

    import app.models as models  # NO reload

    # ✅ tabloları oluştur
    models.Base.metadata.create_all(bind=db.engine)

    import app.main as main
    importlib.reload(main)

    with TestClient(main.app) as c:
        yield c
