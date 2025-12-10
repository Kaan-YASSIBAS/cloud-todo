from dotenv import load_dotenv
load_dotenv()

import os

class Settings:
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "task-service")
    PORT: int = int(os.getenv("PORT", "8002"))

    JWT_SECRET: str = os.getenv("JWT_SECRET", "devsecret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://todo_user:todo_pass@postgres-host:5432/todo_db",
)


    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500,*",
    ).split(",")

settings = Settings()
