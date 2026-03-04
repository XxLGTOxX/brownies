from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from bson import ObjectId
from datetime import datetime

from config import get_db, now_local

router = APIRouter(tags=["clients"])
templates = Jinja2Templates(directory="templates")


def require_auth(request: Request):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=302)
    return None


@router.get("/clientes", response_class=HTMLResponse)
async def list_clients(request: Request):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()
    clients = await db.clients.find().sort("name", 1).to_list(100)
    for c in clients:
        c["id"] = str(c["_id"])
        # backwards compatibility for older records
        if "sells_individual" not in c:
            c["sells_individual"] = c.get("price_individual") is not None
        if "sells_charola" not in c:
            c["sells_charola"] = c.get("price_charola") is not None
    return templates.TemplateResponse("clients.html", {
        "request": request,
        "clients": clients
    })


@router.get("/clientes/nuevo", response_class=HTMLResponse)
async def new_client_form(request: Request):
    auth = require_auth(request)
    if auth:
        return auth
    return templates.TemplateResponse("client_form.html", {
        "request": request,
        "client": None,
        "error": None
    })


@router.post("/clientes")
async def create_client(
    request: Request,
    name: str = Form(...),
    sells_individual: str = Form(""),
    sells_charola: str = Form(""),
    price_individual: float = Form(0),
    price_charola: float = Form(0)
):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()

    existing = await db.clients.find_one({"name": name})
    if existing:
        return templates.TemplateResponse("client_form.html", {
            "request": request,
            "client": {
                "name": name,
                "sells_individual": bool(sells_individual),
                "sells_charola": bool(sells_charola),
                "price_individual": price_individual if sells_individual else '',
                "price_charola": price_charola if sells_charola else ''
            },
            "error": "Ya existe un cliente con ese nombre"
        })

    if not sells_individual and not sells_charola:
        return templates.TemplateResponse("client_form.html", {
            "request": request,
            "client": {
                "name": name,
                "sells_individual": bool(sells_individual),
                "sells_charola": bool(sells_charola),
                "price_individual": price_individual if sells_individual else '',
                "price_charola": price_charola if sells_charola else ''
            },
            "error": "Selecciona al menos un tipo de producto"
        })

    if sells_individual and price_individual <= 0:
        return templates.TemplateResponse("client_form.html", {
            "request": request,
            "client": {
                "name": name,
                "sells_individual": bool(sells_individual),
                "sells_charola": bool(sells_charola),
                "price_individual": price_individual,
                "price_charola": price_charola if sells_charola else ''
            },
            "error": "Ingresa un precio válido para individuales"
        })
    if sells_charola and price_charola <= 0:
        return templates.TemplateResponse("client_form.html", {
            "request": request,
            "client": {
                "name": name,
                "sells_individual": bool(sells_individual),
                "sells_charola": bool(sells_charola),
                "price_individual": price_individual if sells_individual else '',
                "price_charola": price_charola
            },
            "error": "Ingresa un precio válido para charolas"
        })

    doc = {
        "name": name,
        "sells_individual": bool(sells_individual),
        "sells_charola": bool(sells_charola),
        "price_individual": price_individual if sells_individual else None,
        "price_charola": price_charola if sells_charola else None,
        "created_at": now_local()
    }
    await db.clients.insert_one(doc)
    return RedirectResponse(url="/clientes", status_code=302)


@router.get("/clientes/{client_id}/editar", response_class=HTMLResponse)
async def edit_client_form(request: Request, client_id: str):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()
    client = await db.clients.find_one({"_id": ObjectId(client_id)})
    if not client:
        return RedirectResponse(url="/clientes", status_code=302)
    client["id"] = str(client["_id"])
    # Ensure backwards compatibility
    if "sells_individual" not in client:
        client["sells_individual"] = client.get("price_individual") is not None
    if "sells_charola" not in client:
        client["sells_charola"] = client.get("price_charola") is not None
    return templates.TemplateResponse("client_form.html", {
        "request": request,
        "client": client,
        "error": None
    })


@router.post("/clientes/{client_id}")
async def update_client(
    request: Request,
    client_id: str,
    name: str = Form(...),
    sells_individual: str = Form(""),
    sells_charola: str = Form(""),
    price_individual: float = Form(0),
    price_charola: float = Form(0)
):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()

    if not sells_individual and not sells_charola:
        client = await db.clients.find_one({"_id": ObjectId(client_id)})
        if client:
            client["id"] = str(client["_id"])
        return templates.TemplateResponse("client_form.html", {
            "request": request,
            "client": client,
            "error": "Selecciona al menos un tipo de producto"
        })

    if sells_individual and price_individual <= 0:
        client = await db.clients.find_one({"_id": ObjectId(client_id)})
        if client:
            client["id"] = str(client["_id"])
        return templates.TemplateResponse("client_form.html", {
            "request": request,
            "client": client,
            "error": "Ingresa un precio válido para individuales"
        })
    if sells_charola and price_charola <= 0:
        client = await db.clients.find_one({"_id": ObjectId(client_id)})
        if client:
            client["id"] = str(client["_id"])
        return templates.TemplateResponse("client_form.html", {
            "request": request,
            "client": client,
            "error": "Ingresa un precio válido para charolas"
        })

    await db.clients.update_one(
        {"_id": ObjectId(client_id)},
        {"$set": {
            "name": name,
            "sells_individual": bool(sells_individual),
            "sells_charola": bool(sells_charola),
            "price_individual": price_individual if sells_individual else None,
            "price_charola": price_charola if sells_charola else None
        }}
    )
    return RedirectResponse(url="/clientes", status_code=302)


@router.post("/clientes/{client_id}/eliminar")
async def delete_client(request: Request, client_id: str):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()
    await db.clients.delete_one({"_id": ObjectId(client_id)})
    return RedirectResponse(url="/clientes", status_code=302)


@router.get("/api/clientes/{client_id}/precios")
async def get_client_prices(request: Request, client_id: str):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()
    client = await db.clients.find_one({"_id": ObjectId(client_id)})
    if not client:
        return JSONResponse({"error": "Cliente no encontrado"}, status_code=404)
    return JSONResponse({
        "name": client["name"],
        "sells_individual": client.get("sells_individual", True),
        "sells_charola": client.get("sells_charola", True),
        "price_individual": client.get("price_individual") or 0,
        "price_charola": client.get("price_charola") or 0
    })
