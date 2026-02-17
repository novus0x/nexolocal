########## Modules ##########
from db.model import Company

from core.config import settings

from core.http_requests import api_post

from services.tax_engine.utils import get_endpoint, get_tax_engine_credintials

########## Variables ##########
endpoint, routes = get_endpoint("pe")

########## Create Company ##########
async def create_company(company: Company, tax_profile, files):
    ### Variables ###
    token = None
    url = endpoint + routes["auth"]
    account = {
        "username": settings.TAX_ENGINE_USER,
        "password": settings.TAX_ENGINE_PASSWORD
    }

    response = await get_tax_engine_credintials(url, account)

    if response.get("error"):
        if response.get("error") == "Empresa duplicada.":
            return False, "tax_engine.api.duplicated_company" # Se debe dontactar con soporte@apisperu.com

        return False, "tax_engine.system.incorrect_credentials"
    else:
        token = response.get("token")

    if not token:
        return False, "tax_engine.system.incorrect_credentials"

    url2 = endpoint + routes["companies"]["create"]

    company_info = {
        "plan": "free",
        "environment": "beta",
        "sol_user": tax_profile.get("tax_user"),
        "sol_pass": tax_profile.get("tax_password"),
        "ruc": tax_profile.get("tax_id"),
        "razon_social": tax_profile.get("legal_name"),
        "direccion": tax_profile.get("address_line"),
        "certificado": files.get("certificate").decode("utf-8"),
        "logo": files.get("logo").decode("utf-8")
    }

    response = await api_post(url2, company_info, {
        "Authorization": f"Bearer {token}"
    })

    return response, ""
