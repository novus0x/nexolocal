########## Modules ##########
from zoneinfo import ZoneInfo
from datetime import date, timedelta, time, datetime

from fastapi import APIRouter, Request, Depends

from sqlalchemy import func, case, extract, desc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Company, Product, Cash_Session_Status, Cash_Session, Cash_Movement, Cash_Movement_Type, Sale, Sale_Item, Sale_Status, Expense, Expense_Status, Payment_Method

from core.config import settings

from core.i18n import translate
from core.responses import custom_response
from core.permissions import check_permissions

########## Variables ##########
router = APIRouter()
TIMEZONE = settings.TIMEZONE

LOCAL_TZ = ZoneInfo(TIMEZONE)
UTZ_TZ = ZoneInfo("UTC")

########## Company Dashboard - Company ##########
@router.get("/")
async def c_dashboard(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    low_threshold = 1.43
    cash_session_status = False

    now_local = datetime.now(LOCAL_TZ)
    today = now_local.today()

    today_start = datetime.combine(today, time.min, tzinfo=LOCAL_TZ)
    today_end = today_start + timedelta(days=1)

    yesterday_start = today_start - timedelta(days=1)
    yesterday_end = today_start

    start_week = today - timedelta(days=6)
    start_dt = datetime.combine(start_week, time.min, tzinfo=LOCAL_TZ)
    end_dt = today_end

    month_start = today.replace(day=1)
    month_start_dt = datetime.combine(month_start, time.min, tzinfo=LOCAL_TZ)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    month_end_dt = datetime.combine(next_month, time.min, tzinfo=LOCAL_TZ)

    start = datetime.combine(today, time.min)

    sales_today = 0
    expenses_month = 0
    net_today = 0
    tickets_today = 0

    sales_change_percent = 0
    net_percent = 0

    tickets_average_val = 0

    top_products_today = []
    top_produtcs_month = []

    payments_summary = {
        "cash": 0,
        "card": 0,
        "digital": 0
    }

    payment_metrics = {
        "cash": 0,
        "card": 0,
        "digital": 0
    }

    cash_initial = 0
    cash_in_today = 0
    cash_out_today = 0
    current_cash_amount = 0

    month_cash_sessions_data = {
        "cash_month_list": [],
        "total_cash_month": 0,
        "frequency": 0

    }

    cash_month_list = []

    frequency = 0
    total_cash_month = 0
    total_days_closed = 0
    
    weekly_performance = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    if not check_permissions(db, request, "company.read", company_id):
        return custom_response(status_code=400, message=translate(lang, "validation.not_necessary_permission"))
    
    filters = []

    filters = [Product.company_id == company_id]

    urgency_expr = case(
        (
            (Product.low_stock_alert > 0) & (Product.stock >= 0),
            Product.stock / Product.low_stock_alert
        ),
        else_=999999
    )

    low_products_quantity = db.query(func.count(Product.id)).filter(*filters).filter(
        Product.track_inventory == True
    ).filter(urgency_expr < low_threshold).scalar()

    cash_session = db.query(Cash_Session).filter(
        Cash_Session.status == Cash_Session_Status.OPEN,
        Cash_Session.company_id == company_id
    ).first()
    
    if cash_session:
        cash_session_status = True
        today_start = cash_session.opened_at.astimezone(LOCAL_TZ)

        previous_cash_session = db.query(Cash_Session).filter(
            Cash_Session.company_id == company_id,
            Cash_Session.status == Cash_Session_Status.CLOSED,
            Cash_Session.closed_at < cash_session.opened_at
        ).order_by(desc(Cash_Session.closed_at)).first()

        if previous_cash_session:
            yesterday_start = previous_cash_session.opened_at.astimezone(LOCAL_TZ)
            yesterday_end = previous_cash_session.closed_at.astimezone(LOCAL_TZ)
        else:
            yesterday_end = cash_session.opened_at.astimezone(LOCAL_TZ)
            yesterday_start = yesterday_end - timedelta(days=1)

        sales_yesterday = db.query(func.coalesce(func.sum(Sale.total), 0)).filter(
            Sale.company_id == company_id,
            Sale.status == Sale_Status.COMPLETED,
            Sale.date >= yesterday_start,
            Sale.date < yesterday_end
        ).scalar()

        sales_today = db.query(func.coalesce(func.sum(Sale.total), 0)).filter(
            Sale.company_id == company_id,
            Sale.status == Sale_Status.COMPLETED,
            Sale.date >= today_start,
            Sale.date < today_end
        ).scalar()

        tickets_today = db.query(func.count(Sale.id)).filter(
            Sale.company_id == company_id,
            Sale.status == Sale_Status.COMPLETED,
            Sale.date >= today_start,
            Sale.date < today_end
        ).scalar()

        expenses_yesterday = db.query(func.coalesce(func.sum(Expense.total_amount), 0)).filter(
            Expense.company_id == company_id,
            Expense.status == Expense_Status.PAID,
            Expense.date >= yesterday_start,
            Expense.date < yesterday_end
        ).scalar()

        expenses_today = db.query(func.coalesce(func.sum(Expense.total_amount), 0)).filter(
            Expense.company_id == company_id,
            Expense.status == Expense_Status.PAID,
            Expense.date >= today_start,
            Expense.date < today_end
        ).scalar()

        net_today = sales_today - expenses_today
        net_yesterday = sales_yesterday - expenses_yesterday

        if tickets_today > 0:
            tickets_average_val = round(sales_today / tickets_today, 2)
        else:
            tickets_average_val = 0

        if sales_yesterday > 0:
            sales_change_percent = ((sales_today - sales_yesterday) / sales_yesterday) * 100
        else:
            sales_change_percent = 100 if sales_today > 0 else 0

        sales_change_percent = round(sales_change_percent, 2)

        cash_in_today = db.query(func.coalesce(func.sum(Cash_Movement.amount), 0)).filter(
            Cash_Movement.cash_session_id == cash_session.id,
            Cash_Movement.company_id == company_id,
            Cash_Movement.type.in_([Cash_Movement_Type.SALE, Cash_Movement_Type.INCOME]),
        ).scalar()

        cash_out_today = db.query(func.coalesce(func.sum(Cash_Movement.amount), 0)).filter(
            Cash_Movement.cash_session_id == cash_session.id,
            Cash_Movement.company_id == company_id,
            Cash_Movement.type.in_([Cash_Movement_Type.EXPENSE, Cash_Movement_Type.WITHDRAW]),
        ).scalar()

        current_cash_amount = cash_in_today + cash_session.initial_cash - cash_out_today

        rows_in = db.query(
            Cash_Movement.payment_method,
            func.coalesce(func.sum(Cash_Movement.amount), 0).label("total")
        ).filter(
            Cash_Movement.cash_session_id == cash_session.id,
            Cash_Movement.type.in_([
                Cash_Movement_Type.SALE,
                Cash_Movement_Type.INCOME
            ]),
            Cash_Movement.payment_method != None,
        ).group_by(
            Cash_Movement.payment_method
        ).all()

        for method, total in rows_in:
            payments_summary[method.value] = round(float(total), 2)

        cash_initial = cash_session.initial_cash

        rows_out = db.query(
            Cash_Movement.payment_method,
            func.coalesce(func.sum(Cash_Movement.amount), 0).label("total")
        ).filter(
            Cash_Movement.cash_session_id == cash_session.id,
            Cash_Movement.type.in_([
                Cash_Movement_Type.EXPENSE,
                Cash_Movement_Type.WITHDRAW
            ]),
            Cash_Movement.payment_method != None
        ).group_by(
            Cash_Movement.payment_method
        ).all()

        for method, total in rows_out:
            payment_metrics[f"{method.value}"] = round(float(total), 2)

        ### Top Products ###
        raw_top_today = db.query(
            Product.id,
            Product.name,
            func.sum(Sale_Item.quantity).label("total_qty")
        ).join(Sale_Item, Sale_Item.product_id == Product.id).join(Sale, Sale.id == Sale_Item.sale_id).join(Cash_Movement, Cash_Movement.related_sale_id == Sale.id).filter(
            Cash_Movement.cash_session_id == cash_session.id,
            Cash_Movement.type == Cash_Movement_Type.SALE,
            Sale.status == Sale_Status.COMPLETED
        ).group_by(Product.id).order_by(desc("total_qty")).limit(5).all()

        max_qty = raw_top_today[0].total_qty if raw_top_today else 0

        for i, p in enumerate(raw_top_today, start=1):
            percent = 0

            if max_qty > 0:
                percent = round((p.total_qty / max_qty) * 100, 2)

            top_products_today.append({
                "rank": i,
                "id": p.id,
                "name": p.name,
                "total_qty": int(p.total_qty),
                "percent": percent
            })
    
    expenses_month = db.query(func.coalesce(func.sum(Expense.total_amount), 0)).filter(
        Expense.company_id == company_id,
        Expense.status == Expense_Status.PAID,
        Expense.date >= month_start_dt,
        Expense.date < month_end_dt
    ).scalar()

    ### ###
    month_cash_sessions = db.query(Cash_Session).filter(
        Cash_Session.company_id == company_id,
        Cash_Session.status == Cash_Session_Status.CLOSED,
        Cash_Session.closed_at >= month_start_dt,
        Cash_Session.closed_at < month_end_dt
    ).order_by(desc(Cash_Session.closed_at)).all()

    for session in month_cash_sessions:
        final_amount = float(session.counted_cash or session.expected_cash or 0)
        total_cash_month += final_amount
        total_days_closed += 1

        print(session.difference_exists)

        cash_mont_element = {
            "id": session.id,
            "date": session.closed_at.date().strftime("%B %d, %Y").upper(),
            "opened_at": session.opened_at,
            "closed_at": session.closed_at,
            "final_amount": round(final_amount, 2),
            "difference": float(session.difference or 0),
            "has_difference": session.difference_exists
        }

        cash_month_list.append(cash_mont_element)

        days_passed = today.day

        if days_passed > 0:
            frequency = round((total_days_closed / days_passed) * 100, 2)
        else:
            frequency = 0

    month_cash_sessions_data["cash_month_list"] = cash_month_list
    month_cash_sessions_data["total_cash_month"] = round(total_cash_month, 2)
    month_cash_sessions_data["frequency"] = frequency

    ###  ###
    sales_rows = db.query(
        func.date(Sale.date).label("day"),
        func.coalesce(func.sum(Sale.total), 0).label("total")
    ).filter(
        Sale.company_id == company_id,
        Sale.status == Sale_Status.COMPLETED,
        Sale.date >= start_dt,
        Sale.date < end_dt
    ).group_by(func.date(Sale.date)).all()
    
    expenses_rows = db.query(
        func.date(Expense.date).label("day"),
        func.coalesce(func.sum(Expense.total_amount), 0).label("total")
    ).filter(
        Expense.company_id == company_id,
        Expense.status == Expense_Status.PAID,
        Expense.date >= start_dt,
        Expense.date < end_dt
    ).group_by(func.date(Expense.date)).all()

    sales_map = {row.day: float(row.total) for row in sales_rows}
    expenses_map = {row.day: float(row.total) for row in expenses_rows}
    
    week_labels = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]

    for i in range(7):
        d = start_week + timedelta(days=i)

        weekly_performance.append({
            "day": week_labels[d.weekday()],
            "date": d.isoformat(),
            "sales": round(sales_map.get(d, 0), 2),
            "expenses": round(expenses_map.get(d, 0), 2)
        })
        
    return custom_response(status_code=200, message=translate(lang, "company.companies.dashboard.get"), data={
        "products": {
            "low_products_quantity": low_products_quantity
        },
        "company": {
            "cash": {
                "open": cash_session_status,
                "start": cash_initial,
                "in": cash_in_today,
                "out": cash_out_today,
                "current": current_cash_amount,
                "payment_method": payments_summary,
                "payment_metrics": payment_metrics
            },
            "metrics": {
                "sales": sales_today,
                "sales_percent": sales_change_percent,
                "net": net_today,
                "net_percent": net_percent,
                "tickets": tickets_today,
                "tickets_average": tickets_average_val,
                "expenses": expenses_month,

                "month_cash_sessions": month_cash_sessions_data,

                "products": {
                    "top_today": top_products_today,
                },

                "weekly_performance": weekly_performance
            },
        }
    })
