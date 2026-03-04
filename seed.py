"""
Seed script: Creates initial inventory record in MongoDB.
Run once: python seed.py
"""
import asyncio
from datetime import datetime
from config import connect_db, close_db, get_db


async def seed():
    await connect_db()
    db = get_db()

    # Create initial flour inventory if not exists
    inv = await db.inventory.find_one({"item": "harina"})
    if not inv:
        await db.inventory.insert_one({
            "item": "harina",
            "bags": 0,
            "updated_at": datetime.utcnow()
        })
        print("✅ Inventario de harina creado (0 bolsas)")
    else:
        print(f"ℹ️  Inventario ya existe: {inv['bags']} bolsas")

    print("✅ Seed completado")
    print(f"\n🔑 Credenciales de admin:")
    from config import ADMIN_USER, ADMIN_PASS
    print(f"   Usuario: {ADMIN_USER}")
    print(f"   Contraseña: {ADMIN_PASS}")

    await close_db()


if __name__ == "__main__":
    asyncio.run(seed())
