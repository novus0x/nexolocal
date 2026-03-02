########## Modules ##########
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Request, Depends

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Company_Plan, User_Company_Association, User_Role, User, Company, Company_Subscription_Status, Billing_Status, Company_Billing, Plan_Cicle

from core.config import settings

from core.i18n import translate
from core.generator import get_uuid
from core.responses import custom_response
from core.db_management import add_db, update_db
from core.validators import read_json_body, validate_required_fields

from services.payments.main import get_available_payment_providers, create_payment, verify_payment

########## Variables ##########
router = APIRouter()
TIMEZONE = settings.TIMEZONE

LOCAL_TZ = ZoneInfo(TIMEZONE)
UTZ_TZ = ZoneInfo("UTC")

########## Get Plans ##########
@router.get("/plans")
async def get_plans(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    plans = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Get Plans ###
    plans_data = db.query(Company_Plan).order_by(asc(Company_Plan.position)).all()

    for plan in plans_data:
        descriptions_data = plan.description.split("\n")    

        plans.append({
            "id": plan.id,
            "name": plan.name,
            "price": plan.price,
            "description": descriptions_data,
            "highlight": plan.highlight,
            "highlight_title": plan.highlight_title,
            "highlight_subtitle": plan.highlight_subtitle,
            "cycle": plan.plan_cycle
        })

    ### Check Companies Quantity ###
    companies_q = db.query(User_Company_Association).filter(
        User_Company_Association.user_id == user.get("id")
    ).count()
        
    return custom_response(status_code=200, message=translate(lang, "general.billing.plans.get.success"), data={
        "plans": plans,
        "companies_q": companies_q
    })

########## Get Plan ##########
@router.get("/plans/{plan_id}")
async def get_plan_by_id(request: Request, plan_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    plan = {}

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Get Plan ###
    plan_data = db.query(Company_Plan).filter(
        Company_Plan.id == plan_id
    ).first()

    if not plan_data:
        return custom_response(status_code=400, message=translate(lang, "general.billing.plans.get.unique.error"))

    plan = {
        "id": plan_data.id,
        "name": plan_data.name,
        "price": plan_data.price,
        "description": plan_data.description,
        "cycle": plan_data.plan_cycle
    }

    ### Check Companies Quantity ###
    companies_q = db.query(User_Company_Association).filter(
        User_Company_Association.user_id == user.get("id")
    ).count()
        
    return custom_response(status_code=200, message=translate(lang, "general.billing.plans.get.unique.success"), data={
        "plan": plan,
        "companies_q": companies_q
    })

########## Plan Transaction ##########
@router.post("/plans")
async def plan_transaction(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Get Body ###
    plan_transaction_data, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(plan_transaction_data, [
        "plan_id", "name"
    ], lang)

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    ### Verify User Email Verification ###
    user_data = db.query(User).filter(
        User.id == user.get("id")
    ).first()

    if user_data.email_verified == False:
        return custom_response(status_code=400, message=translate(lang, "general.billing.plans.transaction.error.required_email_verification"))

    ### Get Plan ###
    plan_data = db.query(Company_Plan).filter(
        Company_Plan.id == plan_transaction_data.plan_id
    ).first()

    if not plan_data:
        return custom_response(status_code=400, message=translate(lang, "general.billing.plans.transaction.error.plan_does_not_exist"))

    ### Get User Role ###
    user_role = db.query(User_Role).filter(
        User_Role.id == plan_data.role_id
    ).first()

    if not user_role:
        return custom_response(status_code=400, message=translate(lang, "general.billing.plans.transaction.error.role_does_not_exist"), details=required_fields)

    ### Check Companies Quantity ###
    companies_q = db.query(User_Company_Association).filter(
        User_Company_Association.user_id == user.get("id")
    ).count()

    ### Free Trial or Normal Payment ###
    if companies_q == 0:
        ### Create Company ###
        new_company = Company(
            id = get_uuid(db, Company),

            name = plan_transaction_data.name,
            email = user.get("email"),
            plan_type_id = plan_data.id,
        )

        new_company.is_active = True
        new_company.subscription_status = Company_Subscription_Status.TRIAL
        new_company.trial_ends_at = datetime.now(timezone.utc) + relativedelta(months=1)

        ### Create User Association ###
        new_user_company_association = User_Company_Association(
            id = get_uuid(db, User_Company_Association),
            user_id = user_data.id,
            company_id = new_company.id,
            role_id = user_role.id
        )

        ### Create Billing ###
        new_billing = Company_Billing(
            id = get_uuid(db, Company_Billing),

            reference = f"Prueba Gratuita: {plan_data.name} | {new_company.name}",

            amount = 0,
            status = Billing_Status.ACCEPTED,
            paid_at = datetime.now(timezone.utc),
            billing_cycle = Plan_Cicle.MONTHLY,

            company_id = new_company.id,
            plan_id = plan_data.id,
            user_id = user.get("id")
        )

        ### Save To DB ###
        add_db(db, new_company)
        add_db(db, new_user_company_association)
        add_db(db, new_billing)

        return custom_response(status_code=200, message=translate(lang, "general.billing.plans.transaction.success"), data={
            "trial": True,
            "company_id": new_company.id
        })
    
    ### Create Company - No Trial ###
    new_company = Company(
        id = get_uuid(db, Company),

        name = plan_transaction_data.name,
        email = user.get("email"),
        plan_type_id = plan_data.id,
    )

    new_company.is_active = False
    new_company.subscription_status = Company_Subscription_Status.SUSPENDED

    ### New User Association ###
    new_user_company_association = User_Company_Association(
        id = get_uuid(db, User_Company_Association),
        user_id = user_data.id,
        company_id = new_company.id,
        role_id = user_role.id
    )

    ### Create Billing ###
    new_billing = Company_Billing(
        id = get_uuid(db, Company_Billing),

        reference = f"Pago: {plan_data.name} | {new_company.name}",

        amount = plan_data.price,
        status = Billing_Status.PENDING,
        billing_cycle = Plan_Cicle.MONTHLY,

        company_id = new_company.id,
        plan_id = plan_data.id,
        user_id = user.get("id")
    )

    ### Create Payment ###
    providers_name, providers_key = await get_available_payment_providers()
    payment_url, message, token = await create_payment(providers_key[0], plan_data, user.get("email"), new_company.id)

    if not payment_url:
        return custom_response(status_code=400, message=translate(lang, message))
    
    ### Add Token ###
    new_billing.token_id = token

    ### Save to DB ###
    add_db(db, new_company)
    add_db(db, new_user_company_association)
    add_db(db, new_billing)

    return custom_response(status_code=200, message=translate(lang, "general.billing.plans.transaction.success"), data={
        "trial": False,
        "payment_url": payment_url
    })

########## Validate Plan Payment ##########
@router.post("/validate")
async def validate_company_payment(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang

    ### Get Body ###
    billing_validation, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(billing_validation, [
        "token", "company_id"
    ], lang)

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    ### Token ###
    token = billing_validation.token

    providers_name, providers_key = await get_available_payment_providers()

    ### Check Method ###
    if billing_validation.company_id != "no_data":
        company_id = billing_validation.company_id

        company = db.query(Company).filter(
            Company.id == company_id
        ).first()

        if not company:
            return custom_response(status_code=400, message=translate(lang, "general.billing.validate.invalid_company"))

        billing = db.query(Company_Billing).filter(
            Company_Billing.token_id == token,
            Company_Billing.company_id == company_id
        ).first()

        if not billing:
            return custom_response(status_code=400, message=translate(lang, "general.billing.validate.invalid_billing"))

        if billing.status == Billing_Status.ACCEPTED:
            return custom_response(status_code=200, message=translate(lang, "general.billing.validate.success"))

        response, status = await verify_payment(providers_key[0], token) # Status is something like Billing_Status
        
        if not response:
            if not isinstance(status, Billing_Status):
                return custom_response(status_code=400, message=translate(lang, status)) # Here status is text

            billing.status = status

            ### Update DB ###
            update_db(db)

            return custom_response(status_code=400, message=translate(lang, "general.billing.validate.invalid_payment"))
        
        ### Update Values ###
        billing.status = status
        billing.paid_at = datetime.now(timezone.utc)
        
        company.is_active = True
        company.subscription_status = Company_Subscription_Status.ACTIVE
        company.subscription_ends_at = datetime.now(timezone.utc) + relativedelta(months=1)

        ### Update DB ###
        update_db(db)

        ### Response ###
        return custom_response(status_code=200, message=translate(lang, "general.billing.validate.success"))

    return custom_response(status_code=400, message=translate(lang, "general.billing.validate.no_method"))

########## Get Payment History ##########
@router.get("/history")
async def get_payment_history(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    history = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Get History ###
    history_data = db.query(Company_Billing).filter(
        Company_Billing.user_id == user.get("id")
    ).order_by(desc(Company_Billing.date)).limit(10)

    for history_v in history_data:
        history.append({
            "id": history_v.id,
            "reference": history_v.reference,
            "amount": history_v.amount,
            "status": history_v.status,
            "date": {
                "date": history_v.date.astimezone(LOCAL_TZ).strftime("%d %b %Y"),
                "time": history_v.date.astimezone(LOCAL_TZ).strftime("%H:%M")
            }
        })
        
    return custom_response(status_code=200, message=translate(lang, "general.billing.history.get.success"), data={
        "history": history
    })
