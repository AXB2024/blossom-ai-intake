from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import intake_router

app = FastAPI(
    title="Blossom Smart Intake API",
    description="AI-powered triage and cost-transparency service for telehealth onboarding.",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "message": "API is running"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "smart-intake-api"}


app.include_router(intake_router, prefix="/api")
