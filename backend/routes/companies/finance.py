########## Modules ##########
from zoneinfo import ZoneInfo
from datetime import timedelta, datetime, time

from fastapi import APIRouter, Request, Depends

from sqlalchemy import func, literal, desc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Income, Income_Status, Expense, Expense_Category, Expense_Status

from core.config import settings

from core.i18n import translate
from core.generator import get_uuid
from core.db_management import add_db
from core.responses import custom_response
from core.utils import date_label, is_float
from core.validators import read_json_body, validate_required_fields
from core.permissions import check_permissions


########## Variables ##########
router = APIRouter()
TIMEZONE = settings.TIMEZONE

LOCAL_TZ = ZoneInfo(TIMEZONE)
UTZ_TZ = ZoneInfo("UTC")

########## Get Finances - Company ##########
@router.get("/")
async def main(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    limit = 15
    offset = 0 # paginacion

    finance_grouped = {}
    items_v = []

    utility = 0

    days = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.incomes.read", company_id)
    access2, message2 = check_permissions(db, request, "company.expenses.read", company_id)
    
    if not access or not access2:
        return custom_response(status_code=400, message=message)
    
    ### Local Time ###
    now_local = datetime.now(LOCAL_TZ)
    today_local = now_local.date()

    start_dt = datetime.combine(
        today_local - timedelta(days=6),
        time.min,
        tzinfo=LOCAL_TZ
    )

    end_dt = datetime.combine(
        today_local,
        time.max,
        tzinfo=LOCAL_TZ
    )

    income_by_day = (
        db.query(
            func.date(Income.date).label("day"),
            func.coalesce(func.sum(Income.amount), 0).label("total")
        ).filter(
            Income.company_id == company_id,
            Income.date >= start_dt,
            Income.date <= end_dt
        ).group_by(func.date(Income.date)).all()
    )

    expense_by_day = (
        db.query(
            func.date(Expense.date).label("day"),
            func.coalesce(func.sum(Expense.total_amount), 0).label("total"),
        ).filter(
            Expense.company_id == company_id,
            Expense.date >= start_dt,
            Expense.date <= end_dt
        ).group_by(func.date(Expense.date)).all()
    )

    days = [
        (start_dt + timedelta(days=i)).date()
        for i in range(7)
    ]

    income_map = {row.day: float(row.total) for row in income_by_day}
    expense_map = {row.day: float(row.total) for row in expense_by_day}

    chart_days = []

    for day in days:
        chart_days.append({
            "date": day.strftime("%d %b"),
            "income": income_map.get(day, 0),
            "expense": expense_map.get(day, 0)
        })
    
    ## Utility ##
    income_sum = db.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        Income.company_id == company_id
    ).scalar()

    expense_sum = db.query(func.coalesce(func.sum(Expense.total_amount), 0)).filter(
        Expense.company_id == company_id
    ).scalar()

    utility = income_sum - expense_sum

    ## Querys ##
    income_q = db.query(
        Income.id.label("id"),
        literal("income").label("type"),
        Income.name.label("name"),
        Income.amount.label("amount"),
        Income.date.label("date")
    ).filter(
        Income.company_id == company_id
    )

    expense_q = db.query(
        Expense.id.label("id"),
        literal("expense").label("type"),
        Expense.name.label("name"),
        Expense.total_amount.label("amount"),
        Expense.date.label("date")
    ).filter(
        Expense.company_id == company_id
    )

    finance_rows = (
        income_q.union_all(expense_q).order_by(desc("date")).limit(limit).offset(offset).all()
    )

    for row in finance_rows:
        local_date = row.date.astimezone(LOCAL_TZ)
        label = date_label(local_date)

        if label not in finance_grouped:
            finance_grouped[label] = []

        finance_grouped[label].append({
            "id": row.id,
            "type": row.type,
            "name": row.name,
            "amount": row.amount,
            "time": local_date.astimezone(LOCAL_TZ).strftime("%H:%M - %d %b %Y")
        })

    for label, items in finance_grouped.items():
        items_v.append({
            "label": label,
            "items": items
        })

    #  #
    finance = {
        "utility": utility,
        "month_utility": 0,
        "income": income_sum,
        "expense": expense_sum,
        "chart_days": chart_days
    }

    return custom_response(status_code=200, message=translate(lang, "company.finances.get"), data={
        "finance": finance,
        "items": items_v
    })

########## Create new Finance - Company ##########
@router.post("/create")
async def create_finance(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.incomes.create", company_id)
    access2, message2 = check_permissions(db, request, "company.expenses.create", company_id)
    
    if not access or not access2:
        return custom_response(status_code=400, message=message)
    
    ### Get Body ###
    finance_check, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(finance_check, [
        "amount", "title", "description", "expense_category", "subcategory", "date", "receipt_url"
    ])

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    ### Operations ###
    amount = is_float(finance_check.amount)

    if not amount:
        return custom_response(status_code=400, message=translate(lang, "company.finances.create.error_amount"), details=required_fields)
    elif amount == 0:
        return custom_response(status_code=400, message=translate(lang, "company.finances.create.error_amount"), details=required_fields)

    if amount > 0:
        new_finance = Income(
            id = get_uuid(db, Income),
            status = Income_Status.RECEIVED,
            subcategory = finance_check.subcategory,
        )
    else:
        amount *= -1
        new_finance = Expense(
            id = get_uuid(db, Expense),
            status = Expense_Status.PAID,
            total_amount = amount
        )

        try:
            new_finance.category = Expense_Category[finance_check.expense_category]

            if new_finance.category == Expense_Category.OTHER:
                new_finance.subcategory = finance_check.subcategory

        except:
            new_finance.category = Expense_Category.OTHER
            new_finance.subcategory = finance_check.subcategory
    
    new_finance.name = finance_check.title
    new_finance.amount = finance_check.amount
    new_finance.description = finance_check.description 
    new_finance.company_id = company_id
    new_finance.payment_date = finance_check.date
    new_finance.approved_by_id = user.get("id")

    add_db(db, new_finance)
    
    return custom_response(status_code=200, message=translate(lang, "company.finances.create.success"), data={})
