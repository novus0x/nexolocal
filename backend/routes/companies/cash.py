########## Modules ##########
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Depends

from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Cash_Session_Status, Cash_Session, Cash_Movement, Cash_Movement_Type, Payment_Method

from core.i18n import translate
from core.generator import get_uuid
from core.responses import custom_response
from core.db_management import add_db, update_db
from core.validators import read_json_body, validate_required_fields
from core.permissions import check_permissions
from core.utils import is_float

########## Variables ##########
router = APIRouter()

########## Open a new Cash Session - Company ##########
@router.post("/open")
async def open(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "company.cash.open", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)

    cash_session = db.query(Cash_Session).filter(
        Cash_Session.status == Cash_Session_Status.OPEN,
        Cash_Session.company_id == company_id
    ).first()

    if cash_session:
        return custom_response(status_code=400, message=translate(lang, "company.cash.error.already_open"))
    
    ### Get Body ###
    check_cash, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(check_cash, [
        "initial_cash"
    ])

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    initial_cash = is_float(check_cash.initial_cash)

    if not initial_cash:
        return custom_response(status_code=400, message=translate(lang, "company.cash.error.initial_cash"))

    new_cash_session = Cash_Session(
        id = get_uuid(db, Cash_Session),
        initial_cash = initial_cash,

        company_id = company_id,
        opened_by_id = user.get("id")
    )

    add_db(db, new_cash_session)

    return custom_response(status_code=200, message=translate(lang, "company.cash.create.success"), data={})

########## Close Cash Session - Company ##########
@router.post("/close")
async def open(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    difference = 0

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

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "company.cash.close", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    cash_session = db.query(Cash_Session).filter(
        Cash_Session.status == Cash_Session_Status.OPEN,
        Cash_Session.company_id == company_id
    ).first()

    if not cash_session:
        return custom_response(status_code=400, message=translate(lang, "company.cash.close.error.already_close"))
    
    ### Get Body ###
    check_cash, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(check_cash, [
        "amount", "description"
    ])

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    amount = is_float(check_cash.amount)

    if not amount and amount != 0:
        return custom_response(status_code=400, message=translate(lang, "company.cash.close.error.incorrect_amount"), details=required_fields)

    rows = db.query(
        Cash_Movement.payment_method,
        func.coalesce(func.sum(Cash_Movement.amount), 0).label("total")
    ).filter(
        Cash_Movement.cash_session_id == cash_session.id,
        Cash_Movement.type.in_([
            Cash_Movement_Type.SALE,
            Cash_Movement_Type.INCOME
        ]),
        Cash_Movement.payment_method != None
    ).group_by(Cash_Movement.payment_method).all()

    for method, total in rows:
        payments_summary[method.value] = round(float(total), 2)

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
    ).group_by(Cash_Movement.payment_method).all()

    for method, total in rows_out:
        payment_metrics[f"{method.value}"] = round(float(total), 2)

    cash_out = db.query(
        func.coalesce(func.sum(Cash_Movement.amount), 0)
    ).filter(
        Cash_Movement.cash_session_id == cash_session.id,
        Cash_Movement.type.in_([
            Cash_Movement_Type.EXPENSE,
            Cash_Movement_Type.WITHDRAW
        ]),
        Cash_Movement.payment_method == Payment_Method.CASH
    ).scalar()
    
    expected_cash = is_float(payments_summary.get("cash")) + is_float(cash_session.initial_cash) - is_float(payment_metrics.get("cash"))

    if expected_cash != amount:
        difference = (expected_cash - amount) * - 1

        if check_cash.description == "No description":
            return custom_response(status_code=200, message=translate(lang, "company.cash.close.error.require_description"), data={
                "difference": difference,
                "invalid_description": True
            })

    cash_session.counted_cash = amount
    cash_session.difference = difference
    cash_session.expected_cash = expected_cash
    cash_session.status = Cash_Session_Status.CLOSED
    cash_session.description = check_cash.description
    cash_session.closed_at = datetime.now(timezone.utc)

    if difference != 0:
        cash_session.difference_exists = True

    update_db(db)

    return custom_response(status_code=200, message=translate(lang, "company.cash.close.success"), data={
        "difference": difference,
        "invalid_description": False
    })
