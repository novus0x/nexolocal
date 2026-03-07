########## Modules ##########
from zoneinfo import ZoneInfo
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import desc
from sqlalchemy.orm import Session

from db.model import Company, Tax_Profile, Sale, Sale_Item, Product, Tax_Document_Type, Tax_Series

from core.config import settings

from core.generator import get_uuid
from core.db_management import add_db
from core.utils import to_decimal, to_decimal_or_zero
from core.http_requests import api_post, api_get, api_put

from services.tax_engine.utils import get_endpoint, get_tax_engine_credintials, get_tax_rate_util

########## Variables ##########
endpoint, routes = get_endpoint("pe")
tax_rate = get_tax_rate_util("pe")

LOCAL_TZ = ZoneInfo("America/Lima")
UTZ_TZ = ZoneInfo("UTC")

AUTH_URL = endpoint + routes["auth"]
ACCOUNT = {
    "username": settings.TAX_ENGINE_USER,
    "password": settings.TAX_ENGINE_PASSWORD
}

########## Aux Functions ##########
def to_payload_number(value):
    return float(to_decimal_or_zero(value))

async def get_credentials():
    ### Variables ###
    token = None
    
    response = await get_tax_engine_credintials(AUTH_URL, ACCOUNT)

    if response.get("error"):
        return False, "tax_engine.error.incorrect_credentials"
    else:
        token = response.get("token")

    if not token:
        return False, "tax_engine.error.incorrect_credentials"  

    return token.strip(), ""

########## Create Company ##########
async def create_company(company: Company, tax_profile, files):
    ### Credentials ###
    token, message = await get_credentials()

    if not token:
        return False, message

    url = endpoint + routes["companies"]["create"]

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

    response = await api_post(url, company_info, {
        "Authorization": f"Bearer {token}"
    })

    if response.get("error") == "Empresa duplicada.":
        return False, "tax_engine.api.duplicated_company" # Se debe contactar con soporte@apisperu.com

    return response, ""

########## Get Tax Rate ##########
async def get_tax_rate():
    return Decimal(f"{tax_rate}"), ""

########## Switch Company Mode ##########
async def switch_company_mode(company: Company, tax_profile: Tax_Profile):
    ### Variables ###
    url = endpoint + routes["companies"]["get"] + f"/{tax_profile.sub_id}"

    ### Credentials ###
    token, message = await get_credentials()

    if not token:
        return False, message
    
    response = await api_get(url, {}, {
        "Authorization": f"Bearer {token}"
    })

    if response.get("error"):
        return False, "tax_engine.api.switch_mode.error"

    data = response

    result = {
        "plan": data["plan"]["nombre"],
        "environment": "produccion",
        "sol_user": data["sol_user"],
        "sol_pass": data["sol_pass"],
        "ruc": data["ruc"],
        "razon_social": data["razon_social"],
        "direccion": data["direccion"],
        "certificado": data["certificado"],
        "logo": data["logo"],
        "client_id": None if data["client_id"] == "None" else data["client_id"],
        "client_secret": None if data["client_secret"] == "None" else data["client_secret"]
    }

    response = await api_put(url, result, {
        "Authorization": f"Bearer {token}"
    })

    print(response) # idk why only works when print is here...

    if response.get("error"):
        return False, "tax_engine.api.switch_mode.error"

    return True, ""

########## Get Legend ##########
def get_legend(num: Decimal):
    num = Decimal(num).quantize(Decimal("0.01"), ROUND_HALF_UP)

    unidades = (
        "", "UN", "DOS", "TRES", "CUATRO",
        "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE"
    )

    especiales = (
        "DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE",
        "QUINCE", "DIECISEIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE"
    )

    decenas_txt = (
        "", "", "VEINTE", "TREINTA", "CUARENTA",
        "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"
    )

    centenas_txt = (
        "", "CIENTO", "DOSCIENTOS", "TRESCIENTOS",
        "CUATROCIENTOS", "QUINIENTOS", "SEISCIENTOS",
        "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"
    )

    def unidades_func(n):
        return unidades[n]

    def decenas_func(n):
        if n < 10:
            return unidades_func(n)

        if 10 <= n < 20:
            return especiales[n - 10]

        if 20 <= n < 30:
            if n == 20:
                return "VEINTE"
            return "VEINTI" + unidades_func(n % 10)

        d = decenas_txt[n // 10]
        u = unidades_func(n % 10)

        if u:
            return f"{d} Y {u}"

        return d

    def centenas_func(n):
        if n == 100:
            return "CIEN"

        if n < 100:
            return decenas_func(n)

        c = centenas_txt[n // 100]
        r = n % 100

        if r:
            return f"{c} {decenas_func(r)}"

        return c

    def miles_func(n):
        m = n // 1000
        r = n % 1000

        if m == 0:
            return centenas_func(r)
        if m == 1:
            return f"MIL {centenas_func(r)}".strip()
        
        return f"{centenas_func(m)} MIL {centenas_func(r)}".strip()

    def millones_func(n):
        m = n // 1_000_000
        r = n % 1_000_000
        if m == 0:
            return miles_func(r)
        if m == 1:
            return f"UN MILLON {miles_func(r)}".strip()
        return f"{centenas_func(m)} MILLONES {miles_func(r)}".strip()

    enteros = int(num)
    centavos = int((num - enteros) * 100)
    letras = millones_func(enteros)

    return f"SON {letras} CON {centavos:02d}/100 SOLES"

########## Create Receipt ##########
async def create_receipt(db: Session, company: Company, sale: Sale, items: list[Sale_Item], tax_rate: Decimal, send_sale: bool):
    ### Tax Profile ###
    tax_profile = db.query(Tax_Profile).filter(
        Tax_Profile.company_id == company.id
    ).first()

    tax_enabled = tax_profile.tax_enabled

    ### Variables ###
    subtotal = Decimal("0")
    tax_total = Decimal("0")
    total = Decimal("0")

    gravadas = Decimal("0")
    exoneradas = Decimal("0")

    details = []

    ### Logic ###
    for item in items:
        product = db.query(Product).filter(
            Product.id == item.product_id
        ).first()

        quantity = to_decimal(item.quantity)
        price_with_tax = to_decimal(item.unit_price)

        if quantity is None or price_with_tax is None:
            return False, "tax_engine.error.invalid_item_values", None

        if quantity <= 0 or price_with_tax < 0:
            return False, "tax_engine.error.invalid_item_values", None

        ### Check Product Case
        if not tax_enabled or product.exonerated:
            base = price_with_tax
            igv = Decimal("0")

            tip_afec_igv = 20
        else:
            base = price_with_tax / (Decimal(1) + tax_rate)
            igv = price_with_tax - base

            tip_afec_igv = 10

        base = base.quantize(Decimal("0.01"), ROUND_HALF_UP)
        igv = igv.quantize(Decimal("0.01"), ROUND_HALF_UP)

        total_line = base + igv

        ### Update Item ###
        item.line_base_amount = base * quantity
        item.line_tax_amount = igv * quantity
        item.total = total_line * quantity

        subtotal += item.line_base_amount
        tax_total += item.line_tax_amount
        total += item.total

        ### Grav or Exo ###
        if tip_afec_igv == 10:
            gravadas += item.line_base_amount
        else:
            exoneradas += item.line_base_amount

        ### Sunat Details ###
        details.append({
            "codProducto": product.identifier,
            "unidad": "NIU",
            "descripcion": product.name,
            "cantidad": to_payload_number(quantity),
            "mtoValorUnitario": to_payload_number(base),
            "mtoValorVenta": to_payload_number(base * quantity),
            "mtoBaseIgv": to_payload_number(base * quantity),
            "porcentajeIgv": to_payload_number(tax_rate * 100) if tip_afec_igv == 10 else 0.0,
            "igv": to_payload_number(igv * quantity),
            "tipAfeIgv": tip_afec_igv,
            "totalImpuestos": to_payload_number(igv * quantity),
            "mtoPrecioUnitario": to_payload_number(price_with_tax)
        })
    
    ### Update Sale ###
    sale.subtotal = subtotal
    sale.taxable_amount = gravadas
    sale.tax_amount = tax_total
    sale.total = total
    sale.total_amount = total

    ### Get Legend & Address ###
    legend_value = get_legend(sale.total_amount)
    addres_parts = tax_profile.address_line.split(",")

    if (len(addres_parts)) < 5:
        return False, "tax_engine.error.incorrect_address_line", None

    ### Get Series ###
    series_receipt = db.query(Tax_Series).filter(
        Tax_Series.doc_type == Tax_Document_Type.RECEIPT,
        Tax_Series.company_id == company.id
    ).order_by(desc(Tax_Series.date)).first()

    ### Date ###
    emission_date = datetime.now(UTZ_TZ).astimezone(LOCAL_TZ).strftime("%Y-%m-%dT00:00:00-05:00")

    ### Optional Fiscal Customer ###
    customer_doc_type = "1"
    customer_doc_number = sale.client_doc_number or "99999999"
    customer_name = sale.client_name or "VARIOS"

    if sale.client_doc_type == "RUC":
        customer_doc_type = "6"
    elif sale.client_doc_type == "OTRO":
        customer_doc_type = "0"

    ### Sunat Payload ###
    payload = {
        "ublVersion": "2.1",
        "tipoOperacion": "0101",
        "tipoDoc": str(Tax_Document_Type.RECEIPT.value),
        "serie": str(series_receipt.series),
        "correlativo": str(series_receipt.current_number + 1),
        "fechaEmision": emission_date,
        "formaPago": {
            "moneda": "PEN",
            "tipo": "Contado"
        },
        "tipoMoneda": "PEN",
        "client": {
            "tipoDoc": customer_doc_type, # 6 RUC
            "numDoc": customer_doc_number,
            "rznSocial": customer_name,
            "address": {
                "direccion": "Direccion cliente",
                "provincia": "LIMA",
                "departamento": "LIMA",
                "distrito": "LIMA",
                "ubigueo": "150101"
            }
        },
        "company": {
            "ruc": tax_profile.tax_id,
            "razonSocial": tax_profile.legal_name,
            "nombreComercial": company.name,
            "address": {
                "direccion": addres_parts[0].strip(),
                "distrito": addres_parts[1].strip(),
                "provincia": addres_parts[2].strip(),
                "departamento": addres_parts[3].strip(),
                "ubigueo": addres_parts[4].strip()
            }
        },
        "mtoOperGravadas": to_payload_number(gravadas),
        "mtoOperExoneradas": to_payload_number(exoneradas),
        "mtoIGV": to_payload_number(tax_total),
        "valorVenta": to_payload_number(subtotal),
        "totalImpuestos": to_payload_number(tax_total),
        "subTotal": to_payload_number(total),
        "mtoImpVenta": to_payload_number(total),
        "details": details,
        "legends": [
            {
                "code": "1000",
                "value": legend_value
            }
        ]
    }
    
    if send_sale:
        new_receipt_series = Tax_Series(
            id = get_uuid(db, Tax_Series),
            doc_type = Tax_Document_Type.RECEIPT,

            series = series_receipt.series,
            current_number = series_receipt.current_number + 1,

            company_id = company.id
        )
        
        ### Send Request
        url = endpoint + routes["companies"]["invoice"]["send"]
        
        response = await api_post(url, payload, {
            "Authorization": f"Bearer {tax_profile.tax_token}"
        })

        if response.get("error"):
            return False, "tax_engine.error.incorrect_credentials", None # Referencia a sol / certificado / password otro

        sunat_response = response.get("sunatResponse")

        if sunat_response and not sunat_response.get("success"):
            error = sunat_response.get("error", {})

            return False, "tax_engine.error.sunat_error", error.get("message")
        
        ### Add New Receipt ###
        add_db(db, new_receipt_series)

        return response, "", None
    
    else:
        return True, "", None
