########## Modules ##########
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Request, Depends

from sqlalchemy import asc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Company_Plan, User_Company_Association, User_Role, User, Company, Company_Subscription_Status, Billing_Status, Company_Billing, Plan_Cicle

from core.config import settings

from core.i18n import translate
from core.generator import get_uuid
from core.db_management import add_db
from core.responses import custom_response
from core.validators import read_json_body, validate_required_fields

from services.payments.main import get_available_payment_providers, get_payment_fee

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
    
    providers_name, providers_key = await get_available_payment_providers()

    ### Plan Fee ###
    fee = await get_payment_fee(providers_key[0], plan_data.price)

    plan = {
        "id": plan_data.id,
        "name": plan_data.name,
        "price": plan_data.price,
        "description": plan_data.description,
        "cycle": plan_data.plan_cycle,
        "fee": fee
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

    providers_name, providers_key = await get_available_payment_providers()

    ### Get User Role ###
    user_role = db.query(User_Role).filter(
        User_Role.id == plan_data.role_id
    ).first()

    if not user_role:
        return custom_response(status_code=400, message=translate(lang, "general.billing.plans.transaction.error.role_does_not_exist"), details=required_fields)
    
    ### Plan Fee ###
    fee = await get_payment_fee(providers_key[0], plan_data.price)

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

            reference = f"Prueba Gratuita: {new_company.name}",

            amount = 0,
            status = Billing_Status.ACCEPTED,
            paid_at = datetime.now(timezone.utc),
            billing_cycle = Plan_Cicle.MONTHLY,

            company_id = new_company.id,
            plan_id = plan_data.id
        )

        ### Save To DB ###
        add_db(db, new_company)
        add_db(db, new_user_company_association)
        add_db(db, new_billing)

        return custom_response(status_code=200, message=translate(lang, "general.billing.plans.transaction.success"), data={
            "trial": True,
            "company_id": new_company.id
        })

    else:
        print("Redirect to payment page") # Not Implemented
        
    return custom_response(status_code=200, message=translate(lang, "general.billing.plans.transaction.success"), data={
        "trial": False
    })
