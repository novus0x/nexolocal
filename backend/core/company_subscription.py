########## Modules ##########
from datetime import datetime, timezone

from db.model import Company_Subscription_Status

########## Sync Company Subscription ##########
def sync_company_subscription(company):
    if not company:
        return False

    now = datetime.now(timezone.utc)
    updated = False

    ### Suspended ###
    if company.is_suspended:
        if company.subscription_status != Company_Subscription_Status.SUSPENDED:
            company.subscription_status = Company_Subscription_Status.SUSPENDED
            updated = True

        if company.is_active:
            company.is_active = False
            updated = True

        return updated

    ### Trial ###
    if company.subscription_status == Company_Subscription_Status.TRIAL:
        if company.trial_ends_at and company.trial_ends_at <= now:
            if company.is_active:
                company.is_active = False
                updated = True

            if company.subscription_status != Company_Subscription_Status.EXPIRED:
                company.subscription_status = Company_Subscription_Status.EXPIRED
                updated = True
        elif not company.is_active:
            company.is_active = True
            updated = True

    ### Active ###
    elif company.subscription_status == Company_Subscription_Status.ACTIVE:
        if company.subscription_ends_at and company.subscription_ends_at <= now:
            if company.is_active:
                company.is_active = False
                updated = True

            if company.subscription_status != Company_Subscription_Status.EXPIRED:
                company.subscription_status = Company_Subscription_Status.EXPIRED
                updated = True
        elif not company.is_active:
            company.is_active = True
            updated = True

    elif company.subscription_status in (
        Company_Subscription_Status.EXPIRED,
        Company_Subscription_Status.SUSPENDED,
        Company_Subscription_Status.CANCELLED
    ):
        if company.is_active:
            company.is_active = False
            updated = True

    return updated

########## Validate Company Access ##########
def validate_company_access(company, lang, translate):
    if not company:
        return False, translate(lang, "company.companies.verify.no_exist")

    if company.subscription_status == Company_Subscription_Status.EXPIRED:
        return False, translate(lang, "validation.company_expired")

    if company.subscription_status == Company_Subscription_Status.SUSPENDED or company.is_suspended:
        return False, translate(lang, "validation.company_suspended")

    if company.subscription_status == Company_Subscription_Status.CANCELLED or not company.is_active:
        return False, translate(lang, "validation.company_inactive")

    return True, ""
