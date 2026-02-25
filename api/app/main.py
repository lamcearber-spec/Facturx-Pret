"""FastAPI application entry point for Factur-X Prêt API."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Factur-X Prêt API — génère des factures conformes EN 16931 au format Factur-X 1.0.8. "
        "Produit des PDF/A-3 avec XML CII intégré (factur-x.xml)."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Factur-X Prêt API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
