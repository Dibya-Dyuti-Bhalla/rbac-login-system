"""
Seed the database with initial roles, permissions, and an admin user.
Run: python -m app.db.seed
"""
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .session import AsyncSessionLocal, init_db
from ..models.role import Role, Permission, RolePermission, PERMISSIONS, ROLE_PERMISSIONS
from ..models.user import User
from ..models.user_role import UserRole
from ..core.security import get_password_hash


async def seed(db: AsyncSession):
    print("🌱 Seeding permissions...")
    perm_map: dict[str, Permission] = {}
    for name, description in PERMISSIONS.items():
        resource, action = name.split(":", 1)
        result = await db.execute(select(Permission).where(Permission.name == name))
        perm = result.scalar_one_or_none()
        if not perm:
            perm = Permission(name=name, description=description, resource=resource, action=action)
            db.add(perm)
        perm_map[name] = perm
    await db.flush()

    print("🌱 Seeding roles...")
    role_map: dict[str, Role] = {}
    for role_name, perm_names in ROLE_PERMISSIONS.items():
        result = await db.execute(select(Role).where(Role.name == role_name))
        role = result.scalar_one_or_none()
        if not role:
            role = Role(name=role_name, description=f"System {role_name} role", is_system="true")
            db.add(role)
            await db.flush()
        role_map[role_name] = role

        # Assign permissions to role
        for perm_name in perm_names:
            perm = perm_map.get(perm_name)
            if perm:
                result = await db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == perm.id,
                    )
                )
                if not result.scalar_one_or_none():
                    db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    await db.flush()

    print("🌱 Seeding admin user...")
    result = await db.execute(select(User).where(User.email == "admin@kbgplatform.com"))
    admin = result.scalar_one_or_none()
    if not admin:
        admin = User(
            email="admin@kbgplatform.com",
            username="admin",
            full_name="System Administrator",
            hashed_password=get_password_hash("Admin@123456"),
            is_active=True,
            is_superuser=True,
        )
        db.add(admin)
        await db.flush()

        admin_role = role_map["ADMIN"]
        db.add(UserRole(user_id=admin.id, role_id=admin_role.id))

    await db.commit()
    print("✅ Seed complete. Admin login: admin@kbgplatform.com / Admin@123456")


async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())