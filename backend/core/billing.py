########## Modules ##########
import math
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from sqlalchemy import desc

from db.model import User_Company_Association, Company_Subscription_Status, Plan_Cicle

from core.company_subscription import sync_company_subscription
from core.db_management import update_db

########## Get Sort Key for Billing Items ##########
def get_billing_item_sort_key(item):
    return (
        0 if item["expired"] else 1,
        item["days_left"],
        item["company_name"].lower()
    )

########## Get Billing Delta ##########
def get_billing_cycle_delta(cycle):
    if cycle == Plan_Cicle.YEARLY:
        return relativedelta(years=1)

    return relativedelta(months=1)

########## Build Billing Overview ##########
def build_billing_overview(db, user_id, local_tz):
    ### Variables ###
    companies = []
    billing_items = []

    now_utc = datetime.now(timezone.utc)
    has_subscription_updates = False

    ### Get Associations ###
    companies_association_data = db.query(User_Company_Association).filter(
        User_Company_Association.user_id == user_id
    ).order_by(desc(User_Company_Association.date)).all()

    ### Build Data ###
    for association in companies_association_data:
        company = association.company

        if not company:
            continue

        if sync_company_subscription(company):
            has_subscription_updates = True

        company_status = company.subscription_status.value if company.subscription_status else "inactive"
        company_is_accessible = company_status in ("active", "trial") and company.is_active and not company.is_suspended

        companies.append({
            "id": company.id,
            "name": company.name,
            "status": company_status,
            "is_accessible": company_is_accessible
        })

        renewal_date = None

        if company.subscription_status == Company_Subscription_Status.TRIAL:
            renewal_date = company.trial_ends_at
        elif company.subscription_status in (
            Company_Subscription_Status.ACTIVE,
            Company_Subscription_Status.EXPIRED,
            Company_Subscription_Status.CANCELLED
        ):
            renewal_date = company.subscription_ends_at

        if not renewal_date:
            continue

        renewal_date_local = renewal_date.astimezone(local_tz)
        delta_seconds = (renewal_date - now_utc).total_seconds()
        days_left = math.ceil(delta_seconds / 86400) if delta_seconds >= 0 else math.floor(delta_seconds / 86400)

        can_pay_now = False

        if company.company_plan and company.subscription_status in (
            Company_Subscription_Status.ACTIVE,
            Company_Subscription_Status.EXPIRED,
            Company_Subscription_Status.CANCELLED
        ):
            can_pay_now = True

        billing_items.append({
            "type": "renewal",
            "company_id": company.id,
            "company_name": company.name,
            "plan_id": company.plan_type_id,
            "plan_name": company.company_plan.name if company.company_plan else None,
            "amount": company.company_plan.price if company.company_plan else 0,
            "cycle": company.company_plan.plan_cycle.value if company.company_plan else Plan_Cicle.MONTHLY.value,
            "status": company.subscription_status.value,
            "date_label": renewal_date_local.strftime("%d %b %Y"),
            "days_left": days_left,
            "expired": renewal_date <= now_utc,
            "can_pay_now": can_pay_now
        })

    ### Update DB ###
    if has_subscription_updates:
        update_db(db)

    ### Sort Items ###
    billing_items.sort(key=get_billing_item_sort_key)

    ### Next Item ###
    next_item = {
        "available": False
    }

    if len(billing_items) > 0:
        next_item = {
            **billing_items[0],
            "available": True
        }

    return {
        "companies_q": len(companies),
        "companies": companies,
        "billing_overview": {
            "items": billing_items,
            "next_item": next_item,
            "pending_count": len(billing_items)
        }
    }
