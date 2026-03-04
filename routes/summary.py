from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import timedelta

from config import get_db, now_local, to_local

router = APIRouter(tags=["summary"])
templates = Jinja2Templates(directory="templates")


def require_auth(request: Request):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=302)
    return None


from zoneinfo import ZoneInfo
LOCAL_TZ = ZoneInfo("America/Mexico_City")


def get_week_range(date_str: str = None):
    """Get Monday–Sunday range for a given date or current week.

    Returned datetimes are timezone-aware in the local zone so they can
    be compared directly with documents stored using ``now_local()``.
    """
    from datetime import datetime
    if date_str:
        try:
            target = datetime.strptime(date_str, "%Y-%m-%d")
            # treat the parsed date as local midnight
            target = target.replace(tzinfo=LOCAL_TZ)
        except ValueError:
            target = now_local()
    else:
        target = now_local()

    monday = target - timedelta(days=target.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    sunday = monday + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return monday, sunday


@router.get("/corte-semanal", response_class=HTMLResponse)
async def weekly_summary(request: Request, semana: str = None):
    auth = require_auth(request)
    if auth:
        return auth
    db = get_db()

    monday, sunday = get_week_range(semana)

    paid_deliveries = await db.deliveries.find({
        "status": "pagada",
        "paid_at": {"$gte": monday, "$lte": sunday}
    }).sort("paid_at", 1).to_list(500)
    for d in paid_deliveries:
        d["id"] = str(d["_id"])
        d["paid_at"] = to_local(d.get("paid_at")) if d.get("paid_at") else None

    total_sales = sum(d.get("total", 0) for d in paid_deliveries)

    expenses = await db.expenses.find({
        "date": {"$gte": monday, "$lte": sunday}
    }).sort("date", 1).to_list(500)
    for e in expenses:
        e["id"] = str(e["_id"])

    total_expenses = sum(e.get("amount", 0) for e in expenses)

    net_profit = total_sales - total_expenses
    per_partner = net_profit / 2

    prev_week = (monday - timedelta(days=7)).strftime("%Y-%m-%d")
    next_week = (monday + timedelta(days=7)).strftime("%Y-%m-%d")

    return templates.TemplateResponse("summary.html", {
        "request": request,
        "monday": monday,
        "sunday": sunday,
        "paid_deliveries": paid_deliveries,
        "total_sales": round(total_sales, 2),
        "expenses": expenses,
        "total_expenses": round(total_expenses, 2),
        "net_profit": round(net_profit, 2),
        "nahomy": round(per_partner, 2),
        "gera": round(per_partner, 2),
        "prev_week": prev_week,
        "next_week": next_week,
        "current_week": monday.strftime("%Y-%m-%d")
    })
