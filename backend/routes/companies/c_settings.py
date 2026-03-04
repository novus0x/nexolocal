########## Modules ##########
from types import SimpleNamespace
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Request, Depends, UploadFile, File

from sqlalchemy import desc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Company, Company_Plan, Tax_Environment_Type, Tax_Profile, Tax_Document_Type, Tax_Series, Tax_Emission_Status, Tax_Subscription, Tax_Usage, Company_Subscription_Status

from core.i18n import translate
from core.responses import custom_response
from core.permissions import check_permissions
from core.db_management import add_db, update_db
from core.validators import validate_required_fields
from core.security import generate_base_64, decode_base_64
from core.generator import get_uuid, generate_pem_certificate

from services.tax_engine.main import create_company, switch_company_mode

########## Variables ##########
router = APIRouter()

ext_allowed = (".pem", ".p12", ".pfx")

########## Company Information - GET ##########
@router.get("/")
async def get_company_information(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    company_info = {
        "company": {},
        "plan": {
            "available": False
        },
        "tax_profile": {},
        "tax_subscription": {}
    }

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.settings.read", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)

    ### Operations ###
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    if not company:
        return custom_response(status_code=400, message=translate(lang, "company.settings.does_not_exist"))

    company_info["company"] = {
        "id": company.id,
        "country_code": company.country_code,
        "name": company.name,
        "description": company.description,
        "is_formal": company.is_formal,
        "email": company.email,
        "phone": company.phone,
        "address": company.address,
        "active": company.is_active,
        "status": company.subscription_status,
        "business": company.is_business,
    }

    ### Check Plan ###
    company_plan = db.query(Company_Plan).filter(
        Company_Plan.id == company.plan_type_id
    ).first()

    if company_plan:
        company_info["plan"] = {
            "available": True,

            "name": company_plan.name,
            "price": company_plan.price,
            "cicle": company_plan.plan_cycle,
            "is_trial": False
        }

        if company.subscription_status == Company_Subscription_Status.TRIAL:
            company_info["plan"]["is_trial"] = True

    if company.is_formal:
        tax_profile = db.query(Tax_Profile).filter(
            Tax_Profile.company_id == company_id
        ).first()

        tax_subscription = db.query(Tax_Subscription).filter(
            Tax_Subscription.company_id == company_id
        ).first()
        
        invoice_series = db.query(Tax_Series).filter(
            Tax_Series.doc_type == Tax_Document_Type.INVOICE,
            Tax_Series.company_id == company_id
        ).order_by(desc(Tax_Series.date)).first()

        receipt_series = db.query(Tax_Series).filter(
            Tax_Series.doc_type == Tax_Document_Type.RECEIPT,
            Tax_Series.company_id == company_id
        ).order_by(desc(Tax_Series.date)).first()

        company_info["tax_profile"] = {
            "profile": {
                "legal_name": tax_profile.legal_name,
                "tax_id": tax_profile.tax_id,
                "address": tax_profile.address_line,
                "region": tax_profile.region,
                "city": tax_profile.city,
                "postal_code": tax_profile.postal_code,
                "tax_user": decode_base_64(tax_profile.tax_user).decode("utf-8"),
                "tax_enabled": tax_profile.tax_enabled,
                "env": tax_profile.environment
            },
            "series": {
                "invoice": {
                    "series": invoice_series.series,
                    "number": invoice_series.current_number
                },
                "receipt": {
                    "series": receipt_series.series,
                    "number": receipt_series.current_number
                }
            }
        }

        company_info["tax_subscription"] = {
            "mode": tax_subscription.emission_mode.value if tax_subscription else Tax_Emission_Status.AUTO.value
        }

    return custom_response(status_code=200, message=translate(lang, "company.settings.get.success"), data={
        "information": company_info
    })

########## Company Information - POST ##########
@router.post("/update")
async def update_company_information(request: Request, file: UploadFile = File(None), logo: UploadFile = File(None), db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    certificate = None

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.settings.update", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Get Body ###
    form = await request.form()
    company_info = SimpleNamespace(**dict(form))

    required_fields, error = validate_required_fields(company_info, [
        "commercial_name", "description", "email", "phone", "is_formal",
        "legal_name", "tax_id", "address_line", "region", "city", "postal_code",
        "tax_user", "tax_password", "invoice_series", "invoice_number", "receipt_series",
        "receipt_number", "certificate_password", "emission_status", "tax_enabled"
    ], lang)

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)    

    if company_info.emission_status not in Tax_Emission_Status._value2member_map_:
        return custom_response(status_code=400, message=translate(lang, "company.settings.emission_status_mode_not_allowed"))

    ### Operations ###
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    if not company:
        return custom_response(status_code=400, message=translate(lang, "company.settings.does_not_exist"))

    company.name = company_info.commercial_name
    company.email = company_info.email
    
    if company_info.description != "none":
        company.description = company_info.description
    else:
        company.description = None

    if company_info.phone != "none":
        company.phone = company_info.phone
    else:
        company.phone = None

    ### Update Emission Status & IGV Company ###
    if company.is_formal:
        tax_subscription_update = db.query(Tax_Subscription).filter(
            Tax_Subscription.company_id == company_id
        ).first()
        
        tax_profile_update = db.query(Tax_Profile).filter(
            Tax_Profile.company_id == company_id
        ).first()

        ### Change Values ###
        tax_subscription_update.emission_mode = Tax_Emission_Status(company_info.emission_status)

        if company_info.tax_enabled == "1":
            tax_profile_update.tax_enabled = True
        else:
            tax_profile_update.tax_enabled = False
        
    ### Simple Update ###
    update_db(db)

    ### Formal ###
    if company_info.is_formal == "1":
        ### Tax Info ###
        tax_info = vars(company_info).copy()

        ### Remove elements ###
        tax_info.pop("email")
        tax_info.pop("description")
        tax_info.pop("phone")
        tax_info.pop("is_formal")

        tax_user = generate_base_64(tax_info['tax_user'].encode("utf-8"))
        tax_password = generate_base_64(tax_info['tax_password'].encode("utf-8"))

        ### Cerfitication ###
        filename = file.filename.lower()

        if not filename.endswith(ext_allowed):
            return custom_response(status_code=400, message=translate(lang, "company.settings.incorrect_certificate"))

        file_content = await file.read()
        file_password = company_info.certificate_password

        if filename.endswith(".pem"):
            certificate = b"" + file_content
            tax_info.pop("certificate_password")

        elif filename.endswith(".p12") or filename.endswith(".pfx"):
            if file_password == "none":
                return custom_response(status_code=400, message=translate(lang, "company.settings.require_certificate_password"))

            certificate = generate_pem_certificate(file_content, file_password)

            if not certificate:
                return custom_response(status_code=400, message=translate(lang, "company.settings.incorrect_password"))

        ### Check Required Fields ###
        for key, value in tax_info.items():
            if value == "none":
                return custom_response(status_code=400, message=translate(lang, "company.settings.tax_info_required"))

        ### Check if exists
        tax_profile = db.query(Tax_Profile).filter(
            Tax_Profile.company_id == company_id
        ).first()

        if not tax_profile:
            new_tax_profile = Tax_Profile(
                id = get_uuid(db, Tax_Profile),

                legal_name = tax_info["legal_name"],
                address_line = tax_info["address_line"],
                region = tax_info["region"],
                city = tax_info["city"],
                postal_code = tax_info["postal_code"],

                tax_id = tax_info["tax_id"],
                
                tax_user = tax_user.decode("utf-8"),
                tax_password = tax_password.decode("utf-8"),

                company_id = company_id
            )

            new_tax_series_invoice_id = get_uuid(db, Tax_Series)
            new_tax_series_receipt_id = get_uuid(db, Tax_Series)

            while new_tax_series_receipt_id == new_tax_series_invoice_id:
                new_tax_series_receipt_id = get_uuid(db, Tax_Series)

            new_tax_series_invoice = Tax_Series(
                id = new_tax_series_invoice_id,
                doc_type = Tax_Document_Type.INVOICE,

                series = tax_info["invoice_series"],
                current_number = tax_info["invoice_number"],

                company_id = company_id
            )

            new_tax_series_receipt = Tax_Series(
                id = new_tax_series_receipt_id,
                doc_type = Tax_Document_Type.RECEIPT,

                series = tax_info["receipt_series"],
                current_number = tax_info["receipt_number"],

                company_id = company_id
            )

            new_tax_subscription = Tax_Subscription(
                id = get_uuid(db, Tax_Subscription),
                end_date = datetime.now(timezone.utc) + relativedelta(months=1),

                company_id = company_id
            )

            ### Logo ###
            logo_content = await logo.read()
            logo_base64 = generate_base_64(b"" + logo_content)

            files = {
                "certificate": certificate,
                "logo": logo_base64
            }

            result, message = await create_company(db, company_id, tax_info, files)

            if not result:
                return custom_response(status_code=400, message=translate(lang, message))
            
            sub_id = result["id"]
            token = result["token"]["code"]

            new_tax_profile.sub_id = sub_id
            new_tax_profile.tax_token = token

            add_db(db, new_tax_profile)
            add_db(db, new_tax_series_invoice)
            add_db(db, new_tax_series_receipt)
            add_db(db, new_tax_subscription)

            ### Update Company Formal Status
            company.is_formal = True
            update_db(db)   
                            
        else:
            tax_profile.legal_name = tax_info["legal_name"]
            tax_profile.address_line = tax_info["address_line"]
            tax_profile.region = tax_info["region"]
            tax_profile.city = tax_info["city"]
            tax_profile.postal_code = tax_info["postal_code"]

            tax_profile.tax_id = tax_info["tax_id"]

            tax_profile.tax_user = tax_user.decode("utf-8")
            tax_profile.tax_password = tax_password.decode("utf-8")

            ### Check Series ###
            check_invoice_series = db.query(Tax_Series).filter(
                Tax_Series.doc_type == Tax_Document_Type.INVOICE,
                Tax_Series.company_id == company_id
            ).order_by(desc(Tax_Series.date)).first()
            
            check_receipt_series = db.query(Tax_Series).filter(
                Tax_Series.doc_type == Tax_Document_Type.RECEIPT,
                Tax_Series.company_id == company_id
            ).order_by(desc(Tax_Series.date)).first()

            ### Update ###
            update_db(db)

            ### Series Check Update ###
            if check_invoice_series.series != tax_info["invoice_series"] or check_invoice_series.current_number != tax_info["invoice_number"]:
                new_tax_series_invoice = Tax_Series(
                    id = get_uuid(db, Tax_Series),
                    doc_type = Tax_Document_Type.INVOICE,

                    series = tax_info["invoice_series"],
                    current_number = tax_info["invoice_number"],

                    company_id = company_id
                )

                add_db(db, new_tax_series_invoice)
            
            if check_receipt_series.series != tax_info["receipt_series"] or check_receipt_series.current_number != tax_info["receipt_number"]:
                new_tax_series_receipt = Tax_Series(
                    id = get_uuid(db, Tax_Series),
                    doc_type = Tax_Document_Type.RECEIPT,

                    series = tax_info["receipt_series"],
                    current_number = tax_info["receipt_number"],

                    company_id = company_id
                )

                add_db(db, new_tax_series_receipt)

    return custom_response(status_code=200, message=translate(lang, "company.settings.update.success"))

########## Production Tax System - POST ##########
@router.post("/production-tax-system")
async def production_tax_system(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.settings.update", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Verify Company ###
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    if not company:
        return custom_response(status_code=400, message=translate(lang, "validation.settings.production_tax_system.error"))
    
    ### Verify Tax Profile ###
    tax_profile = db.query(Tax_Profile).filter(
        Tax_Profile.company_id == company.id
    ).first()

    if not tax_profile:
        return custom_response(status_code=400, message=translate(lang, "validation.settings.production_tax_system.error"))
    
    if tax_profile.environment == Tax_Environment_Type.SANDBOX:
        tax_profile.environment = Tax_Environment_Type.PRODUCTION
        
        response, message = await switch_company_mode(db, company_id, tax_profile)

        if not response:
            return custom_response(status_code=400, message=translate(lang, "validation.settings.production_tax_system.error"))
            
        update_db(db)

    return custom_response(status_code=200, message=translate(lang, "company.settings.production_tax_system.success"))
