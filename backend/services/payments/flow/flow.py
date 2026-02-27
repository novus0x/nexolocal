########## Modules ##########
from core.utils import to_decimal_or_zero, to_money

from services.payments.utils import _settings

########## Variables ##########
IGV = to_decimal_or_zero(_settings["flow"]["igv"])
FLOW_FIXED = to_decimal_or_zero(_settings["flow"]["fixed"])
FLOW_PERCENT = to_decimal_or_zero(_settings["flow"]["percent"])

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
