from __future__ import annotations
import click
from flask.cli import with_appcontext
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import hash_password 

@click.command("seed")
@with_appcontext
def seed_db() -> None:
    
    print("Iniciando o processo de seed...")

    if not Tenant.objects(name="Sylo Corp").first():
        tenant = Tenant(
            name="Sylo Corp",
            slug="sylo-corp",
            plan="enterprise",
            contact_email="marcelo@sylo.com.br"

        ).save()
        print(f"Tenant '{tenant.name}' criado com sucesso.")
    else:
        tenant = Tenant.objects(name="Sylo Corp").first()
        print("Tenant inicial já existe.")

    admin_email = "admin@gmail.com"
    if not User.objects(email=admin_email).first():
        User(
            email=admin_email,
            name="Administrador Global",
            password_hash=hash_password("admin123"),
            role="ADMIN",
            tenant=tenant,
            email_verified=True
        ).save()
        print(f"Usuário admin '{admin_email}' criado com sucesso.")
    else:
        print("Usuário admin já existe.")

    print("Seed finalizado.")