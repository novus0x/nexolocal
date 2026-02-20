########## Modules ##########
from services.payments.utils import get_payment_methods, get_engine

########## Variables ##########

########## Get Payment Methods ##########
async def get_available_payment_providers():
    names, values = await get_payment_methods()

    return names, values

########## Get Payment Fee ##########
async def get_payment_fee(payment_provider: str, amount):
    engine, message = await get_engine(payment_provider)

    if not engine:
        return False, message

    fee = await engine.calculate_fee(amount)

    return fee
