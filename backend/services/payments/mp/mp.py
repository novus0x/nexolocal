########## Modules ##########
from decimal import Decimal

from core.config import settings

from services.payments.utils import _settings

########## Variables ##########
BASE_URL = _settings["mp"]["base_url"]

IGV = Decimal(f"{_settings["mp"]["igv"]}")
MP_FIXED = Decimal(f"{_settings["mp"]["fixed"]}")
MP_PERCENT = Decimal(f"{_settings["mp"]["percent"]}")
MP_EFFECTIVE_PERCENT = MP_PERCENT * (Decimal("1") + IGV)

MP_TOKEN = settings.MERCADO_PAGO_ACCESS_TOKEN

########## Calculation Fee ##########
async def calculate_fee(net_amount: float):
    ### Calculate
    gross = (net_amount + MP_FIXED) / (1 - MP_EFFECTIVE_PERCENT)
    fee = gross - net_amount

    return round(fee, 2)
