from sqlalchemy.orm import Session

from src.core.database import SessionLocal
from src.models.permission import Permission
from src.models.role_permission import RolePermission

ALL_PERMISSIONS = [
    {"codename": "owner:read", "description": "Listar e ver donos"},
    {"codename": "owner:write", "description": "Criar, editar e arquivar donos"},
    {"codename": "pet:read", "description": "Listar e ver animais"},
    {"codename": "pet:write", "description": "Criar, editar e arquivar animais"},
    {"codename": "appointment:read", "description": "Listar e ver consultas"},
    {"codename": "appointment:write", "description": "Criar, editar e cancelar consultas"},
    {"codename": "treatment:read", "description": "Listar e ver tratamentos"},
    {"codename": "treatment:write", "description": "Criar e corrigir tratamentos"},
    {"codename": "clinical:read", "description": "Consultar o histórico clínico"},
    {"codename": "clinical:write", "description": "Registar vacinas e medicamentos"},
    {"codename": "waiting:read", "description": "Consultar a sala de espera"},
    {"codename": "waiting:write", "description": "Gerir entradas e estados da sala de espera"},
    {"codename": "service_type:read", "description": "Consultar tipos de serviço"},
    {"codename": "service_type:write", "description": "Configurar tipos de serviço"},
    {"codename": "exam_catalog:read", "description": "Consultar catálogo de exame físico"},
    {"codename": "exam_catalog:write", "description": "Configurar catálogo de exame físico"},
    {"codename": "invoice:read", "description": "Listar e ver faturas"},
    {"codename": "invoice:write", "description": "Criar, editar e cancelar faturas"},
    {"codename": "user:read", "description": "Listar e ver utilizadores"},
    {"codename": "user:write", "description": "Gerir funções dos utilizadores"},
]

ROLE_PERMISSIONS = {
    "admin": [p["codename"] for p in ALL_PERMISSIONS],
    "vet": [
        "owner:read", "owner:write",
        "pet:read", "pet:write",
        "appointment:read", "appointment:write",
        "treatment:read", "treatment:write",
        "clinical:read", "clinical:write",
        "waiting:read", "waiting:write", "service_type:read", "exam_catalog:read",
        "invoice:read", "invoice:write",
    ],
    "receptionist": [
        "owner:read", "owner:write",
        "pet:read", "pet:write",
        "appointment:read", "appointment:write",
        "clinical:read",
        "waiting:read", "waiting:write", "service_type:read", "exam_catalog:read",
        "invoice:read", "invoice:write",
    ],
}


def seed_permissions(db: Session):
    existing = {p.codename: p for p in db.query(Permission).all()}
    for pdata in ALL_PERMISSIONS:
        if pdata["codename"] not in existing:
            perm = Permission(**pdata)
            db.add(perm)
        elif existing[pdata["codename"]].description != pdata["description"]:
            existing[pdata["codename"]].description = pdata["description"]

    db.flush()

    existing = {p.codename: p for p in db.query(Permission).all()}
    existing_rp = db.query(RolePermission).all()
    permission_names = {permission.id: permission.codename for permission in existing.values()}
    for role_permission in existing_rp:
        allowed = ROLE_PERMISSIONS.get(role_permission.role)
        if allowed is not None and permission_names.get(role_permission.permission_id) not in allowed:
            db.delete(role_permission)
    db.flush()
    existing_rp = db.query(RolePermission).all()
    rp_set = {(rp.role, rp.permission_id) for rp in existing_rp}

    for role, codenames in ROLE_PERMISSIONS.items():
        for codename in codenames:
            perm = existing.get(codename)
            if perm and (role, perm.id) not in rp_set:
                db.add(RolePermission(role=role, permission_id=perm.id))

    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_permissions(db)
        print("Permissions seeded successfully.")
    finally:
        db.close()
