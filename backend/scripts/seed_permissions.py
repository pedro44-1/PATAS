from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.permission import Permission
from app.models.role_permission import RolePermission


ALL_PERMISSIONS = [
    {"codename": "owner:read", "description": "Listar e ver donos"},
    {"codename": "owner:write", "description": "Criar, editar e remover donos"},
    {"codename": "pet:read", "description": "Listar e ver animais"},
    {"codename": "pet:write", "description": "Criar, editar e remover animais"},
    {"codename": "appointment:read", "description": "Listar e ver consultas"},
    {"codename": "appointment:write", "description": "Criar, editar e remover consultas"},
    {"codename": "treatment:read", "description": "Listar e ver tratamentos"},
    {"codename": "treatment:write", "description": "Criar, editar e remover tratamentos"},
    {"codename": "invoice:read", "description": "Listar e ver faturas"},
    {"codename": "invoice:write", "description": "Criar, editar e remover faturas"},
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
        "invoice:read", "invoice:write",
    ],
    "receptionist": [
        "owner:read", "owner:write",
        "pet:read", "pet:write",
        "appointment:read", "appointment:write",
        "invoice:read",
    ],
}


def seed_permissions(db: Session):
    existing = {p.codename: p for p in db.query(Permission).all()}
    for pdata in ALL_PERMISSIONS:
        if pdata["codename"] not in existing:
            perm = Permission(**pdata)
            db.add(perm)

    db.flush()

    existing = {p.codename: p for p in db.query(Permission).all()}
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