########## Modules ##########
from core.config import settings
from core.utils import to_decimal_or_zero, to_money

from services.payments.utils import _settings

########## Variables ##########
BASE_URL = _settings["mp"]["base_url"]

IGV = to_decimal_or_zero(_settings["mp"]["igv"])
MP_FIXED = to_decimal_or_zero(_settings["mp"]["fixed"])
MP_PERCENT = to_decimal_or_zero(_settings["mp"]["percent"])
MP_EFFECTIVE_PERCENT = MP_PERCENT * (to_decimal_or_zero(1) + IGV)

MP_TOKEN = settings.MERCADO_PAGO_ACCESS_TOKEN

########## Calculation Fee ##########
async def calculate_fee(net_amount):
    net_amount = to_decimal_or_zero(net_amount)

    ### Calculate
    denominator = to_decimal_or_zero(1) - MP_EFFECTIVE_PERCENT

    if denominator <= 0:
        return to_money(0)

    gross = (net_amount + MP_FIXED) / denominator
    fee = gross - net_amount

    return to_money(fee)
