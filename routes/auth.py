from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from config import ADMIN_USER, ADMIN_PASS, get_db

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = request.session.get("user")
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": None
    })


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["user"] = username
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Usuario o contraseña incorrectos"
    })


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    db = get_db()

    total_clients = await db.clients.count_documents({})
    pending_deliveries = await db.deliveries.count_documents({"status": "pendiente"})

    pipeline = [
        {"$match": {"status": "pendiente"}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}}}
    ]
    pending_result = await db.deliveries.aggregate(pipeline).to_list(1)
    pending_total = pending_result[0]["total"] if pending_result else 0

    inv = await db.inventory.find_one({"item": "harina"})
    bags = inv["bags"] if inv else 0

    # Get recent deliveries for activity feed
    recent = await db.deliveries.find().sort("created_at", -1).to_list(5)
    for r in recent:
        r["id"] = str(r["_id"])

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "total_clients": total_clients,
        "pending_deliveries": pending_deliveries,
        "pending_total": pending_total,
        "bags": round(bags, 2),
        "recent": recent
    })
