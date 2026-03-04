from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import math

from config import get_db, now_local, to_local

router = APIRouter(tags=["inventory"])
templates = Jinja2Templates(directory="templates")


def require_auth(request: Request):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=302)
    return None


@router.get("/inventario", response_class=HTMLResponse)
async def view_inventory(request: Request):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()
    inv = await db.inventory.find_one({"item": "harina"})
    bags = inv["bags"] if inv else 0
    # Floor to ensure integer display
    bags = math.floor(bags)
    updated_at = to_local(inv.get("updated_at")) if inv and inv.get("updated_at") else None
    possible_individuals = int(bags * 9)
    possible_charolas = int(bags)
    return templates.TemplateResponse("inventory.html", {
        "request": request,
        "bags": bags,
        "possible_individuals": possible_individuals,
        "possible_charolas": possible_charolas,
        "updated_at": updated_at
    })


@router.post("/inventario/ajustar")
async def adjust_inventory(
    request: Request,
    bags: float = Form(...),
    reason: str = Form("")
):
    auth = require_auth(request)
    if auth:
        return auth
    
    # Floor the input to integer
    bags = math.floor(bags)
    
    db = get_db()
    inv = await db.inventory.find_one({"item": "harina"})
    if inv:
        new_bags = max(0, inv["bags"] + bags)
        await db.inventory.update_one(
            {"item": "harina"},
            {"$set": {"bags": new_bags, "updated_at": now_local()}}
        )
    else:
        await db.inventory.insert_one({
            "item": "harina",
            "bags": max(0, bags),
            "updated_at": now_local()
        })
    return RedirectResponse(url="/inventario", status_code=302)


@router.post("/inventario/establecer")
async def set_inventory(
    request: Request,
    bags: float = Form(...),
    reason: str = Form("")
):
    auth = require_auth(request)
    if auth:
        return auth
    
    # Floor the input to integer
    bags = math.floor(max(0, bags))
    
    db = get_db()
    await db.inventory.update_one(
        {"item": "harina"},
        {"$set": {"bags": bags, "updated_at": now_local()}},
        upsert=True
    )
    return RedirectResponse(url="/inventario", status_code=302)
