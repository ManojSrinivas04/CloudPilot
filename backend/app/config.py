import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Project root directory: Finops_AI/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env file if it exists in the project root
load_dotenv(PROJECT_ROOT / ".env")

# Paths to data and models
MODELS_DIR = PROJECT_ROOT / "models"
ML_DIR = PROJECT_ROOT / "ml"

MODEL_FILE_PATH = MODELS_DIR / "cloud_model.pkl"
FEATURES_FILE_PATH = MODELS_DIR / "model_features.pkl"

VM_CATALOG_PATH = ML_DIR / "vm_catalog.csv"
STORAGE_CATALOG_PATH = ML_DIR / "storage_catalog.csv"
REGION_PRICING_PATH = ML_DIR / "region_pricing.csv"


class Settings:
    PROJECT_NAME: str = "FinOps AI Cost Optimizer API"
    PROJECT_DESCRIPTION: str = (
        "REST API to predict cloud compute resources and recommend "
        "cost-effective virtual machines across AWS, Azure, and GCP."
    )
    VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api"

    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:change-me@localhost:5432/finops_ai"
    )

    # JWT Authentication settings
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "default-insecure-finops-jwt-secret-key-change-in-production-3849102"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8501",  # Streamlit
    ]


settings = Settings()
