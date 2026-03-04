from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from bson import ObjectId
from datetime import datetime

from config import get_db, now_local

router = APIRouter(tags=["expenses"])
templates = Jinja2Templates(directory="templates")


def require_auth(request: Request):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=302)
    return None


@router.get("/gastos", response_class=HTMLResponse)
async def list_expenses(request: Request):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()
    expenses = await db.expenses.find().sort("date", -1).to_list(200)
    for e in expenses:
        e["id"] = str(e["_id"])
    total = sum(e.get("amount", 0) for e in expenses)
    return templates.TemplateResponse("expenses.html", {
        "request": request,
        "expenses": expenses,
        "total": total
    })


@router.get("/gastos/nuevo", response_class=HTMLResponse)
async def new_expense_form(request: Request):
    auth = require_auth(request)
    if auth:
        return auth
    return templates.TemplateResponse("expense_form.html", {
        "request": request,
        "error": None
    })


@router.post("/gastos")
async def create_expense(
    request: Request,
    description: str = Form(...),
    amount: float = Form(...),
    date: str = Form(...)
):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()
    await db.expenses.insert_one({
        "description": description,
        "amount": amount,
        "date": datetime.strptime(date, "%Y-%m-%d"),
        "created_at": now_local()
    })
    return RedirectResponse(url="/gastos", status_code=302)


@router.post("/gastos/{expense_id}/eliminar")
async def delete_expense(request: Request, expense_id: str):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()
    await db.expenses.delete_one({"_id": ObjectId(expense_id)})
    return RedirectResponse(url="/gastos", status_code=302)
