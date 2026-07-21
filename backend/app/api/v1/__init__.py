from fastapi import APIRouter
from app.api.v1 import auth, owners, pets, appointments, treatments, invoices, users, dashboard

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(owners.router, prefix="/owners", tags=["owners"])
router.include_router(pets.router, prefix="/pets", tags=["pets"])
router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
router.include_router(treatments.router, prefix="/treatments", tags=["treatments"])
router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
