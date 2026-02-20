########## Modules ##########
import json, importlib

########## Variables ##########
_settings = json.load(open("services/payments/settings.json"))

########## Get Available Methods ##########
async def get_payment_methods():
    payment_methods_name = []

    payment_methods_abr = list(_settings.keys())

    for abr_method in payment_methods_abr:
        payment_methods_name.append(_settings[abr_method]["name"])

    return payment_methods_name, payment_methods_abr

########## Get Engine ##########
async def get_engine(payment_provider: str):
    payment_provider = payment_provider.lower()

    provider_names, providers_keys = await get_payment_methods()

    if not payment_provider in providers_keys:
        return False, "payments.error.payment_provider_not_available"

    try:
        engine = importlib.import_module(f"services.payments.{payment_provider}.{payment_provider}")

        return engine, ""
    except:
        return False, "payments.error.creating_engine"
