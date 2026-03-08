########## Modules ##########
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request, Depends

from sqlalchemy import or_, desc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Active_Service, Active_Service_Status, Product_Service_Duration, Company_Customer

from core.config import settings

from core.i18n import translate
from core.responses import custom_response
from core.permissions import check_permissions
from core.generator import get_uuid
from core.db_management import add_db
from core.validators import read_json_body
from core.utils import is_int, pagination, normalize_search, to_decimal

########## Variables ##########
router = APIRouter()
TIMEZONE = settings.TIMEZONE
LOCAL_TZ = ZoneInfo(TIMEZONE)

########## Check Manage Access ##########
def check_manage_access(db: Session, request: Request, company_id: str):
    access, message = check_permissions(db, request, "company.sales.create", company_id)

    if access:
        return True, message

    return check_permissions(db, request, "company.active_services.update", company_id)

########## Save Company Customer ##########
def save_company_customer(db: Session, company_id: str, client_data: dict):
    ### Variables ###
    customer = None

    client_name = (client_data.get("name") or "").strip()
    client_email = (client_data.get("email") or "").strip()
    client_phone = (client_data.get("phone") or "").strip()
    client_doc_type = (client_data.get("doc_type") or "").strip().upper()
    client_doc_number = (client_data.get("doc_number") or "").strip()

    ### Search Priority ###
    if client_doc_type and client_doc_number:
        customer = db.query(Company_Customer).filter(
            Company_Customer.company_id == company_id,
            Company_Customer.doc_type == client_doc_type,
            Company_Customer.doc_number == client_doc_number
        ).first()

    if not customer and client_email:
        customer = db.query(Company_Customer).filter(
            Company_Customer.company_id == company_id,
            Company_Customer.email == client_email
        ).first()

    if not customer and client_phone:
        customer = db.query(Company_Customer).filter(
            Company_Customer.company_id == company_id,
            Company_Customer.phone == client_phone
        ).first()

    ### Create ###
    if not customer:
        customer = Company_Customer(
            id = get_uuid(db, Company_Customer),
            company_id = company_id
        )

    ### Update Values ###
    if client_name:
        customer.name = client_name

    if client_email:
        customer.email = client_email

    if client_phone:
        customer.phone = client_phone

    if client_doc_type:
        customer.doc_type = client_doc_type

    if client_doc_number:
        customer.doc_number = client_doc_number

    add_db(db, customer)

    return customer

########## Calculate Active Service Expiration ##########
def calculate_active_service_expiration(starts_at: datetime, duration, duration_type):
    ### Variables ###
    duration_value = to_decimal(duration)

    if duration_value is None or duration_type == Product_Service_Duration.SESSIONS:
        return None

    if duration_type == Product_Service_Duration.MINUTES:
        return starts_at + timedelta(minutes=float(duration_value))
    if duration_type == Product_Service_Duration.HOURS:
        return starts_at + timedelta(hours=float(duration_value))
    if duration_type == Product_Service_Duration.DAYS:
        return starts_at + timedelta(days=float(duration_value))
    if duration_type == Product_Service_Duration.WEEKS:
        return starts_at + timedelta(weeks=float(duration_value))
    if duration_type == Product_Service_Duration.MONTHS:
        return starts_at + relativedelta(months=int(duration_value))
    if duration_type == Product_Service_Duration.YEARS:
        return starts_at + relativedelta(years=int(duration_value))

    return None

########## Sync Active Service Status ##########
def sync_active_service_status(active_service: Active_Service):
    ### Variables ###
    now = datetime.now(timezone.utc)

    if active_service.status == Active_Service_Status.CANCELLED:
        return active_service.status

    if active_service.customer_id is None:
        active_service.status = Active_Service_Status.NO_CUSTOMER
        return active_service.status

    if active_service.starts_at is None:
        active_service.status = Active_Service_Status.PENDING
        return active_service.status

    if active_service.duration_type == Product_Service_Duration.SESSIONS:
        if active_service.sessions_total is not None and active_service.sessions_used >= active_service.sessions_total:
            active_service.status = Active_Service_Status.EXHAUSTED
        else:
            active_service.status = Active_Service_Status.ACTIVE
    else:
        if active_service.expires_at and active_service.expires_at <= now:
            active_service.status = Active_Service_Status.EXPIRED
        else:
            active_service.status = Active_Service_Status.ACTIVE

    return active_service.status

########## Serialize Active Service ##########
def serialize_active_service(active_service: Active_Service):
    ### Variables ###
    customer_name = active_service.customer.name if active_service.customer and active_service.customer.name else "Venta Mostrador"
    customer_reference = active_service.customer.doc_number if active_service.customer and active_service.customer.doc_number else "Sin cliente"
    sale_reference = active_service.sale.invoice_number if active_service.sale and active_service.sale.invoice_number else active_service.sale_id

    mode = "sessions" if active_service.duration_type == Product_Service_Duration.SESSIONS else "time"

    sessions_label = None
    progress_value = None

    if mode == "sessions" and active_service.sessions_total:
        sessions_label = f"{active_service.sessions_used:02d} / {active_service.sessions_total:02d}"
        progress_value = int((active_service.sessions_used / active_service.sessions_total) * 100) if active_service.sessions_total > 0 else 0

    expires_label = "Pendiente de uso"
    if active_service.duration_type == Product_Service_Duration.SESSIONS:
        expires_label = "Por sesiones"
    elif active_service.expires_at:
        expires_label = active_service.expires_at.astimezone(LOCAL_TZ).strftime("%d %b %Y")

    starts_label = "Pendiente de uso"
    if active_service.starts_at:
        starts_label = active_service.starts_at.astimezone(LOCAL_TZ).strftime("%d %b %Y")

    return {
        "id": active_service.id,
        "sale_id": active_service.sale_id,
        "sale_reference": sale_reference,
        "sale_item_id": active_service.sale_item_id,
        "customer_name": customer_name,
        "customer_reference": customer_reference,
        "service_name": active_service.name,
        "mode": mode,
        "status": active_service.status.value if active_service.status else "pending",
        "sessions_label": sessions_label,
        "progress_value": progress_value,
        "expires_at": expires_label,
        "starts_at": starts_label
    }

########## Count Active Services ##########
def count_company_active_services(db: Session, company_id: str):
    return db.query(Active_Service).filter(
        Active_Service.company_id == company_id,
        Active_Service.status == Active_Service_Status.ACTIVE
    ).count()

########## Get Active Services ##########
@router.get("/")
async def get_active_services(request: Request, page = 1, status = "all", type_of = "all", q = None, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    services_data = []

    ### Pagination ###
    page = is_int(page)

    if not page:
        page = 1

    limit = 12
    page = max(page, 1)
    offset = (page - 1) * limit

    ### Search ###
    search = normalize_search(q)

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.active_services.read", company_id)

    if not access:
        return custom_response(status_code=400, message=message)

    ### Query ###
    filters = [Active_Service.company_id == company_id]

    if type_of == "sessions":
        filters.append(Active_Service.duration_type == Product_Service_Duration.SESSIONS)
    elif type_of == "time":
        filters.append(Active_Service.duration_type != Product_Service_Duration.SESSIONS)

    if search:
        filters.append(
            or_(
                Active_Service.name.ilike(f"%{search}%"),
                Active_Service.sale_id.ilike(f"%{search}%"),
                Company_Customer.name.ilike(f"%{search}%"),
                Company_Customer.email.ilike(f"%{search}%"),
                Company_Customer.phone.ilike(f"%{search}%"),
                Company_Customer.doc_number.ilike(f"%{search}%")
            )
        )

    active_services = (
        db.query(Active_Service)
        .outerjoin(Company_Customer, Company_Customer.id == Active_Service.customer_id)
        .filter(*filters)
        .order_by(desc(Active_Service.date))
        .all()
    )

    ### Sync Status ###
    changed = False

    for active_service in active_services:
        current_status = active_service.status
        next_status = sync_active_service_status(active_service)

        if current_status != next_status:
            changed = True

    if changed:
        db.commit()

    ### Status Filter ###
    if status != "all":
        status_map = {
            "pending": Active_Service_Status.PENDING,
            "active": Active_Service_Status.ACTIVE,
            "expired": Active_Service_Status.EXPIRED,
            "exhausted": Active_Service_Status.EXHAUSTED,
            "no_customer": Active_Service_Status.NO_CUSTOMER,
        }

        if status in status_map:
            active_services = [item for item in active_services if item.status == status_map[status]]

    total_items = len(active_services)
    paged_services = active_services[offset:offset + limit]

    ### Stats ###
    active_quantity = len([item for item in active_services if item.status == Active_Service_Status.ACTIVE])
    expired_quantity = len([item for item in active_services if item.status == Active_Service_Status.EXPIRED])

    for item in paged_services:
        services_data.append(serialize_active_service(item))

    return custom_response(status_code=200, message="Active services", data={
        "items_quantity": total_items,
        "active_quantity": active_quantity,
        "expired_quantity": expired_quantity,
        "services": services_data,
        "pagination": pagination(total_items, limit, offset)
    })

########## Validate Active Service ##########
@router.post("/validate/{active_service_id}")
async def validate_active_service(active_service_id: str, request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_manage_access(db, request, company_id)

    if not access:
        return custom_response(status_code=400, message=message)

    ### Get Active Service ###
    active_service = db.query(Active_Service).filter(
        Active_Service.id == active_service_id,
        Active_Service.company_id == company_id
    ).first()

    if not active_service:
        return custom_response(status_code=400, message="Servicio no encontrado")

    sync_active_service_status(active_service)

    if active_service.status == Active_Service_Status.NO_CUSTOMER:
        return custom_response(status_code=400, message="Primero vincula un cliente")

    if active_service.status == Active_Service_Status.CANCELLED:
        return custom_response(status_code=400, message="El servicio esta cancelado")

    if active_service.status == Active_Service_Status.EXPIRED:
        return custom_response(status_code=400, message="El servicio ya vencio")

    if active_service.status == Active_Service_Status.EXHAUSTED:
        return custom_response(status_code=400, message="El servicio ya fue consumido por completo")

    ### Validate Use ###
    now = datetime.now(timezone.utc)

    if active_service.starts_at is None:
        active_service.starts_at = now
        active_service.expires_at = calculate_active_service_expiration(now, active_service.duration, active_service.duration_type)

    if active_service.duration_type == Product_Service_Duration.SESSIONS:
        if active_service.sessions_total is not None and active_service.sessions_used >= active_service.sessions_total:
            active_service.status = Active_Service_Status.EXHAUSTED
            db.commit()
            return custom_response(status_code=400, message="El servicio ya fue consumido por completo")

        active_service.sessions_used += 1

    active_service.last_validated_at = now
    sync_active_service_status(active_service)

    db.commit()
    db.refresh(active_service)

    return custom_response(status_code=200, message="Servicio validado correctamente", data={
        "service": serialize_active_service(active_service),
        "active_quantity": count_company_active_services(db, company_id)
    })

########## Link Customer To Active Service ##########
@router.post("/link_customer/{active_service_id}")
async def link_customer_to_active_service(active_service_id: str, request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_manage_access(db, request, company_id)

    if not access:
        return custom_response(status_code=400, message=message)

    ### Get Active Service ###
    active_service = db.query(Active_Service).filter(
        Active_Service.id == active_service_id,
        Active_Service.company_id == company_id
    ).first()

    if not active_service:
        return custom_response(status_code=400, message="Servicio no encontrado")

    ### Read Body ###
    link_customer, error = await read_json_body(request)

    if error:
        return custom_response(status_code=400, message=error)

    customer_name = (getattr(link_customer, "name", "") or "").strip()
    customer_email = (getattr(link_customer, "email", "") or "").strip()
    customer_phone = (getattr(link_customer, "phone", "") or "").strip()
    customer_doc_type = (getattr(link_customer, "doc_type", "") or "").strip().upper()
    customer_doc_number = (getattr(link_customer, "doc_number", "") or "").strip()

    if not customer_name:
        return custom_response(status_code=400, message="El nombre del cliente es obligatorio")

    if customer_doc_number and not customer_doc_type:
        return custom_response(status_code=400, message="Completa el tipo de documento")

    customer = save_company_customer(db, company_id, {
        "name": customer_name,
        "email": customer_email,
        "phone": customer_phone,
        "doc_type": customer_doc_type,
        "doc_number": customer_doc_number
    })

    active_service.customer_id = customer.id
    sync_active_service_status(active_service)

    db.commit()
    db.refresh(active_service)

    return custom_response(status_code=200, message="Cliente vinculado correctamente", data={
        "service": serialize_active_service(active_service),
        "active_quantity": count_company_active_services(db, company_id)
    })
