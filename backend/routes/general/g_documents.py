########## Modules ##########
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request, Depends

from sqlalchemy import desc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Sale, Sale_Item, Company, Tax_Profile, Tax_Document

from core.config import settings

from core.i18n import translate
from core.responses import custom_response

########## Variables ##########
router = APIRouter()
TIMEZONE = settings.TIMEZONE

LOCAL_TZ = ZoneInfo(TIMEZONE)

########## Public Check Ticket ##########
@router.get("/check-ticket")
async def public_check_ticket(request: Request, q: str = "", db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    query = (q or "").strip()

    sale = None
    tax_document = None

    items = []

    ### Validations ###
    if not query:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=[{
            "message": "El codigo del comprobante es obligatorio."
        }])

    if "-" in query:
        series, number = query.rsplit("-", 1)

        if number.isdigit():
            tax_document = db.query(Tax_Document).filter(
                Tax_Document.series.ilike(series.strip()),
                Tax_Document.number == int(number)
            ).order_by(desc(Tax_Document.date)).first()

    if tax_document:
        sale = db.query(Sale).filter(
            Sale.id == tax_document.sale_id
        ).first()
    else:
        sale = db.query(Sale).filter(
            Sale.invoice_number.ilike(query)
        ).order_by(desc(Sale.date)).first()

        if sale:
            tax_document = db.query(Tax_Document).filter(
                Tax_Document.sale_id == sale.id
            ).order_by(desc(Tax_Document.date)).first()
    
    if not sale:
        return custom_response(status_code=400, message=translate(lang, "general.documents.error.not_found"))

    ### Check Company ###
    company = db.query(Company).filter(
        Company.id == sale.company_id
    ).first()

    if not company:
        return custom_response(status_code=400, message=translate(lang, "general.documents.error.company_not_found"))

    ### Check Tax Profile ###
    tax_profile = db.query(Tax_Profile).filter(
        Tax_Profile.company_id == company.id
    ).first()

    items_data = db.query(Sale_Item).filter(
        Sale_Item.sale_id == sale.id
    ).all()

    for item in items_data:
        items.append({
            "name": item.name,
            "quantity": item.quantity,
            "price": item.unit_price,
            "base_amount": item.line_base_amount,
            "tax_amount": item.line_tax_amount,
            "total": item.total,
            "is_service": item.is_service,
            "is_bulk": item.product.is_bulk if item.product else False
        })

    tax_document_information = None

    ### Tax Document ###
    if tax_document:
        issue_date = tax_document.issue_date.astimezone(LOCAL_TZ) if tax_document.issue_date else None
        tax_document_information = {
            "id": tax_document.id,
            "doc_type": tax_document.doc_type,
            "series": tax_document.series,
            "number": tax_document.number,
            "invoice": f"{tax_document.series}-{tax_document.number}",
            "status": tax_document.status.value if tax_document.status else None,
            "customer_name": tax_document.customer_name,
            "customer_tax_id_type": tax_document.customer_tax_id_type,
            "customer_tax_id": tax_document.customer_tax_id,
            "subtotal": tax_document.subtotal,
            "tax_total": tax_document.tax_total,
            "total": tax_document.total,
            "hash": tax_document.hash,
            "pdf_url": tax_document.artifact_pdf_url,
            "has_xml": True if tax_document.artifact_xml else False,
            "issue_date": issue_date.strftime("%H:%M - %d %b %Y") if issue_date else None,
        }

    local_date = sale.date.astimezone(LOCAL_TZ)

    company_information = {
        "name": company.name,
        "legal_name": tax_profile.legal_name if tax_profile else company.name,
        "tax_id": tax_profile.tax_id if tax_profile else None,
        "phone": company.phone,
        "address": company.address,
        "is_formal": company.is_formal,
    }

    sale_information = {
        "id": sale.id,
        "invoice": tax_document_information["invoice"] if tax_document_information else sale.invoice_number,
        "internal_invoice": sale.invoice_number,
        "items": items,
        "subtotal": sale.subtotal,
        "taxable_amount": sale.taxable_amount,
        "tax": sale.tax_amount,
        "total": sale.total,
        "currency": sale.currency,
        "date": local_date.strftime("%H:%M - %d %b %Y"),
        "client_name": sale.client_name,
        "client_doc_type": sale.client_doc_type,
        "client_doc_number": sale.client_doc_number,
        "tax_document": tax_document_information,
    }

    return custom_response(status_code=200, message=translate(lang, "general.documents.get.success"), data={
        "company": company_information,
        "sale": sale_information
    })
