########## Modules ##########
import json, importlib

from core.http_requests import api_post

########## Variables ##########
_settings = json.load(open("services/tax_engine/settings.json"))

########## Get Available Countries ##########
def get_countries():
    countries = list(_settings.keys())

    return countries

########## Get Country Endpoint ##########
def get_endpoint(country_code: str):
    endpoint = _settings[country_code]["api"]["base"]
    routes = _settings[country_code]["api"]["routes"]

    return endpoint, routes

########## Get Engine ##########
def get_engine(country_code: str):
    country_code = country_code.lower()

    countries = get_countries()

    if not country_code in countries:
        return False, "tax_engine.error.country_not_available"

    try:
        engine = importlib.import_module(f"services.tax_engine.{country_code}.{country_code}")

        return engine, ""
    except:
        return False, "tax_engine.error.creating_engine"

########## Get Credentials ##########
async def get_tax_engine_credintials(url: str, data):
    response = await api_post(url, data)

    return response

########## Get Tax Rate ##########
async def get_tax_rate_util(country_code: str):
    tax_rate = _settings[country_code]["percentage"]

    return tax_rate
