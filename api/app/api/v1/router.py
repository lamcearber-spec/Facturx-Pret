"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, invoice

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(invoice.router)
