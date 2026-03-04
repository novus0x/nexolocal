########## Modules ##########
import hashlib, hmac

from db.model import Company_Plan, Billing_Status

from core.config import settings

from core.http_requests import api_post_form, api_get
from core.utils import to_decimal_or_zero, to_money

from services.payments.utils import _settings

########## Variables ##########
FLOW_BASE_URL = _settings["flow"]["base_url"]
URL_CONFIRMATION = _settings["flow"]["confirmation_url_path"]
URL_REDIRECTION = _settings["flow"]["redirection_url_path"]

IGV = to_decimal_or_zero(_settings["flow"]["igv"])
FLOW_FIXED = to_decimal_or_zero(_settings["flow"]["fixed"])
FLOW_PERCENT = to_decimal_or_zero(_settings["flow"]["percent"])

########## Flow Aux Functions ##########
def flow_sign(data: dict):
    ### Variables ###
    secret = settings.FLOW_SECRET_KEY

    ### Sign ###
    keys = sorted(data.keys())
    to_sign = ""

    for key in keys:
        to_sign += key + str(data[key])

    signature = hmac.new(
        secret.encode(),
        to_sign.encode(),
        hashlib.sha256
    ).hexdigest()

    return signature

########## Fee function ##########
async def calculate_fee(net):
    net = to_decimal_or_zero(net)
    gross = net

    for _ in range(10):
        percent = to_money(gross * FLOW_PERCENT)
        base = percent + FLOW_FIXED
        igv = to_money(base * IGV)
        fee = base + igv
        gross = net + fee

    return to_money(fee)

########## Create Payment ##########
async def create_payment(plan: Company_Plan, user_email, company_id, commerce_order = None, return_path = None):
    ### Variables ###
    url = FLOW_BASE_URL + "/payment/create"

    final_commerce_order = commerce_order if commerce_order else company_id
    final_return_path = return_path if return_path else f"{URL_REDIRECTION}/plans/{plan.id}/validate?company_id={company_id}"
    
    data = {
        "apiKey": settings.FLOW_API_KEY,
        "commerceOrder": str(final_commerce_order),
        "subject": f"Nexolocal - {plan.name}",
        "currency": "PEN",
        "amount": str(plan.price),
        "email": user_email,
        "urlConfirmation": f"{settings.MAIN_DOMAIN}{URL_CONFIRMATION}?company_id={company_id}",
        "urlReturn": f"{settings.MAIN_DOMAIN}{final_return_path}"
    }

    ### Sign ###
    signature = flow_sign(data)
    data["s"] = signature

    ### Request ###
    response = await api_post_form(url, data)

    if "url" not in response:
        return False, "tax_engine.error.creating_subscription", None
    
    ### Build Redirection URL ###
    url = response.get("url")
    token = response.get("token")

    redirection_url = f"{url}?token={token}"

    return redirection_url, "", token

########## Verify Payment ##########
async def verify_payment(token):
    ### Variables ###
    url = FLOW_BASE_URL + "/payment/getStatus"

    params = {
        "apiKey": settings.FLOW_API_KEY,
        "token": token
    }

    ### Sign ###
    signature = flow_sign(params)
    params["s"] = signature

    ### Request ###
    response = await api_get(url, params)

    ### ACCEPTED ###
    if response.get("status") == 2:
        return True, Billing_Status.ACCEPTED
    
    ### REJECTED ###
    if response.get("status") == 3:
        return False, Billing_Status.REJECTED
    
    ### CANCELLED ###
    if response.get("status") == 4:
        return False, Billing_Status.REJECTED

    return False, "tax_engine.error.getting_payment"
