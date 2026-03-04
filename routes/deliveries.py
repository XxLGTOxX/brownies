from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from bson import ObjectId

from config import get_db, now_local, to_local

router = APIRouter(tags=["deliveries"])
templates = Jinja2Templates(directory="templates")

# Business rules:
# 1 charola = 9 brownies = 1 bolsa de harina
# 18 individuales = 2 bolsas de harina -> 1 individual = 2/18 bolsas
BAGS_PER_INDIVIDUAL = 2 / 18  # ~0.1111 bolsas por pieza
BAGS_PER_CHAROLA = 1.0        # 1 bolsa por charola


def require_auth(request: Request):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=302)
    return None


@router.get("/entregas", response_class=HTMLResponse)
async def list_deliveries(request: Request, status: str = "todas"):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()

    query = {}
    if status == "pendiente":
        query["status"] = "pendiente"
    elif status == "pagada":
        query["status"] = "pagada"

    deliveries = await db.deliveries.find(query).sort("created_at", -1).to_list(200)
    for d in deliveries:
        d["id"] = str(d["_id"])
        # convert timestamps from UTC to local zone for correct display
        d["created_at"] = to_local(d.get("created_at"))
        if d.get("paid_at"):
            d["paid_at"] = to_local(d["paid_at"])

    return templates.TemplateResponse("deliveries.html", {
        "request": request,
        "deliveries": deliveries,
        "current_status": status
    })


@router.get("/entregas/nueva", response_class=HTMLResponse)
async def new_delivery_form(request: Request):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()
    clients = await db.clients.find().sort("name", 1).to_list(100)
    for c in clients:
        c["id"] = str(c["_id"])
    # check for simple error indicator in query string
    error = None
    if request.query_params.get("error") == "tipo_no_disponible":
        error = "El tipo de producto seleccionado no está disponible para ese cliente"
    return templates.TemplateResponse("delivery_form.html", {
        "request": request,
        "clients": clients,
        "error": error
    })


@router.post("/entregas")
async def create_delivery(
    request: Request,
    client_id: str = Form(...),
    product_type: str = Form(...),
    quantity: int = Form(...)
):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()

    client = await db.clients.find_one({"_id": ObjectId(client_id)})
    if not client:
        return RedirectResponse(url="/entregas/nueva", status_code=302)

    # ensure product type is sold by this client
    if product_type == "individual" and not client.get("sells_individual", True):
        # return to form with error (could look up by id again)
        return RedirectResponse(url=f"/entregas/nueva?error=tipo_no_disponible", status_code=302)
    if product_type == "charola" and not client.get("sells_charola", True):
        return RedirectResponse(url=f"/entregas/nueva?error=tipo_no_disponible", status_code=302)

    if product_type == "individual":
        unit_price = client.get("price_individual") or 0
        bags_used = quantity * BAGS_PER_INDIVIDUAL
    else:
        unit_price = client.get("price_charola") or 0
        bags_used = quantity * BAGS_PER_CHAROLA

    total = quantity * unit_price

    await db.deliveries.insert_one({
        "client_id": str(client["_id"]),
        "client_name": client["name"],
        "product_type": product_type,
        "quantity": quantity,
        "unit_price": unit_price,
        "total": total,
        "status": "pendiente",
        "paid_at": None,
        "created_at": now_local()
    })

    inv = await db.inventory.find_one({"item": "harina"})
    if inv:
        new_bags = max(0, inv["bags"] - bags_used)
        await db.inventory.update_one(
            {"item": "harina"},
            {"$set": {"bags": new_bags, "updated_at": now_local()}}
        )
    else:
        await db.inventory.insert_one({
            "item": "harina",
            "bags": max(0, -bags_used),
            "updated_at": now_local()
        })

    return RedirectResponse(url="/entregas", status_code=302)


@router.post("/entregas/{delivery_id}/pagar")
async def mark_as_paid(request: Request, delivery_id: str):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()
    await db.deliveries.update_one(
        {"_id": ObjectId(delivery_id)},
        {"$set": {
            "status": "pagada",
            "paid_at": now_local()
        }}
    )
    return RedirectResponse(url="/entregas", status_code=302)


@router.post("/entregas/{delivery_id}/pendiente")
async def mark_as_pending(request: Request, delivery_id: str):
    """Revert a delivery to pendiente in case of mistake."""
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()
    await db.deliveries.update_one(
        {"_id": ObjectId(delivery_id)},
        {"$set": {
            "status": "pendiente",
            "paid_at": None
        }}
    )
    return RedirectResponse(url="/entregas", status_code=302)


@router.post("/entregas/{delivery_id}/eliminar")
async def delete_delivery(request: Request, delivery_id: str):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()
    await db.deliveries.delete_one({"_id": ObjectId(delivery_id)})
    return RedirectResponse(url="/entregas", status_code=302)
