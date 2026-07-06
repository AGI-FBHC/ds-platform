from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config import settings
from app.db_schema import ensure_runtime_schema
from app.models import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)
ensure_runtime_schema(engine)

app = FastAPI(
    title="AGI&FBHC DataSphere API",
    description="Dataset Management Platform API",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {"message": "Welcome to AGI&FBHC DataSphere API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
