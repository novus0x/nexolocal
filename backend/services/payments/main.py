########## Modules ##########
from db.model import Company_Plan

from services.payments.utils import get_payment_methods, get_engine

########## Variables ##########

########## Get Payment Methods ##########
async def get_available_payment_providers():
    names, values = await get_payment_methods()

    return names, values

########## Get Payment Fee ##########
async def get_payment_fee(payment_provider: str, amount):
    ### Get Engine ###
    engine, message = await get_engine(payment_provider)

    if not engine:
        return False, message

    ### Calculate Fee ###
    fee = await engine.calculate_fee(amount)

    return fee

########## Create Payment ##########
async def create_payment(payment_provider: str, plan: Company_Plan, user_email, company_id):
    ### Get Engine ###
    engine, message = await get_engine(payment_provider)

    if not engine:
        return False, message, None

    ### Create Subscription ###
    result, message, token = await engine.create_payment(plan, user_email, company_id)

    if not result:
        return False, message, None

    return result, "", token

########## Verify Payment ##########
async def verify_payment(payment_provider: str, token):
    ### Get Engine ###
    engine, message = await get_engine(payment_provider)

    if not engine:
        return False, message

    ### Verify Payment ###
    result, status = await engine.verify_payment(token)

    if not result:
        return False, status

    return result, status
