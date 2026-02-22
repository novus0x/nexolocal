########## Modules ##########
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from sqlalchemy import desc
from sqlalchemy.orm import Session

from db.model import Company, Sale, Sale_Item, Tax_Emission_Status, Tax_Subscription_Plan, Tax_Subscription, Tax_Usage, Tax_Document_Type

from core.config import settings
from core.generator import get_uuid
from core.db_management import add_db, update_db

from services.tax_engine.utils import get_plan_limit, get_engine, get_tax_engine_credintials

########## Create Company ##########
async def create_company(db: Session, company_id, tax_profile, files):
    ### Get Engine ###
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    country_code = company.country_code.lower()

    engine, message = get_engine(country_code)

    if not engine:
        return False, message
    
    ### Call Specific Function ###
    response, message = await engine.create_company(company, tax_profile, files)

    if not response:
        return False, message

    return response, ""

########## Get Tax Rate ##########
async def get_tax_rate(db: Session, company_id):
    ### Get Engine ###
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    country_code = company.country_code.lower()

    engine, message = get_engine(country_code)

    if not engine:
        return False, message
    
    ### Get Tax Function ###
    response, _ = await engine.get_tax_rate()

    return response, ""

########## Receipt & Invoice Usage ##########
async def receipt_invoice_usage(db: Session, company_id):
    ### Variables
    now = datetime.now(timezone.utc)
    year, month = now.year, now.month

    expired = False

    ### Subscription ###
    subscription = db.query(Tax_Subscription).filter(
        Tax_Subscription.is_active == True,
        Tax_Subscription.company_id == company_id
    ).order_by(desc(Tax_Subscription.date)).first()
 
    if subscription:
        expired = subscription.end_date <= now            
    
    if not subscription or expired: # FIX UPDATE COMPANY FROM PREMIUM TO FREE - API
        new_tax_subscription = Tax_Subscription(
            id = get_uuid(db, Tax_Subscription),
            end_date = now + relativedelta(months=1),
            company_id = company_id
        )

        if expired:
            subscription.is_active = False
            new_tax_subscription.emission_mode = subscription.emission_mode

            ### Update DB ###
            update_db(db)

        ### Add to DB ###
        add_db(db, new_tax_subscription)

        subscription = new_tax_subscription

    ### Check Usage ###
    usage = db.query(Tax_Usage).filter(
        Tax_Usage.company_id == company_id,
        Tax_Usage.year == year,
        Tax_Usage.month == month
    ).first()

    if not usage:
        new_usage = Tax_Usage(
            id =get_uuid(db, Tax_Usage),
            year = year,
            month = month,
            emissions_count = 0,
            company_id = company_id
        )

        ### Add to DB ###
        add_db(db, new_usage)

        usage = new_usage

    ### Check Limits ###
    limit = get_plan_limit(subscription.plan_type)
    used = usage.emissions_count or 0

    if limit is None: # Unlimited
        return True, "", None
    
    remaining = limit - used

    print(remaining)

    if remaining <= 0:
        return False, "tax_engine.error.plan_limit_reached", [{
            "code": "plan_limit_reached",
            "limit": limit,
            "used": used,
            "remaining": 0,
            "year": year,
            "month": month
        }]

    return True, "", None

########## Create Receipt ##########
async def create_receipt(db: Session, company_id, sale: Sale, items: list[Sale_Item], send_sale: bool, invoice_method: str):
    ### Variables ###
    response = False

    ### Get Engine ###
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    country_code = company.country_code.lower()

    engine, message = get_engine(country_code)

    if not engine:
        return False, message, None
    
    ### Get Tax Rate ###
    tax_rate, message = await get_tax_rate(db, company_id)

    if not tax_rate:
        return False, message, None
    
    ### Validation ###
    subscription = db.query(Tax_Subscription).filter(
        Tax_Subscription.company_id == company_id
    ).order_by(desc(Tax_Subscription.date)).first()


    if subscription.emission_mode == Tax_Emission_Status.AUTO: #### RECEIPT
        invoice_method = Tax_Document_Type.RECEIPT ### Verify

        send_sale = True

    else:
        print("TO-DO")

    ### Check Usage availability ###
    usage, message, details = await receipt_invoice_usage(db, company_id)

    if not usage and send_sale:
        return False, message, details

    ### Call Specific Function ###
    if invoice_method == Tax_Document_Type.RECEIPT:
        response, message, details = await engine.create_receipt(db, company, sale, items, tax_rate, send_sale)
            
    else:
        print("TO-DO: INVOICE METHOD")

    if not response:
        return False, message, details
    
    if response and send_sale:
        ### Update Tax Usage ###
        now = datetime.now(timezone.utc)

        usage = db.query(Tax_Usage).filter(
            Tax_Usage.company_id == company_id,
            Tax_Usage.year == now.year,
            Tax_Usage.month == now.month
        ).first()

        if usage:
            usage.emissions_count = (usage.emissions_count or 0) + 1

    ### Update DB ###
    update_db(db)

    return response, "", None
