from fastapi import APIRouter

from src.api import (
    appointments,
    auth,
    clinical,
    dashboard,
    encounters,
    exam_catalog,
    invoices,
    owners,
    pets,
    service_types,
    treatments,
    users,
    waiting_room,
    whatsapp,
)

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(owners.router, prefix="/owners", tags=["owners"])
router.include_router(pets.router, prefix="/pets", tags=["pets"])
router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
router.include_router(treatments.router, prefix="/treatments", tags=["treatments"])
router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(clinical.router, tags=["clinical-history"])
router.include_router(service_types.router, prefix="/service-types", tags=["service-types"])
router.include_router(waiting_room.router, prefix="/waiting-room", tags=["waiting-room"])
router.include_router(exam_catalog.router, prefix="/exam-catalog", tags=["exam-catalog"])
router.include_router(encounters.router, prefix="/appointments", tags=["clinical-records"])
router.include_router(whatsapp.router, prefix="/integrations/whatsapp", tags=["whatsapp"])
