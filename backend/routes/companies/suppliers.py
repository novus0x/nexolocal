########## Modules ##########
from fastapi import APIRouter, Request, Depends

from sqlalchemy import or_, desc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Supplier_Type, Supplier

from core.i18n import translate
from core.generator import get_uuid
from core.db_management import add_db
from core.responses import custom_response
from core.permissions import check_permissions
from core.validators import read_json_body, validate_required_fields
from core.utils import is_int, pagination, normalize_search

########## Variables ##########
router = APIRouter()

########## Create Product ##########
@router.get("/")
async def get_supplies(request: Request, page = 1, type_of = "all", q = None, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    suppliers = []

    ### Params ###
    page = is_int(page)

    if not page:
        page = 1

    limit = 12
    page = max(page, 1)
    offset = (page - 1) * limit

    if type_of != "all":
        if not type_of in Supplier_Type._value2member_map_:
            type_of = "all"

    if q:
        q = q.strip()
        
        if len(q) < 2:
            q = None

    search = normalize_search(q)

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.suppliers.read", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Filters ###
    filters = [
        Supplier.company_id == company_id
    ]

    if type_of != "all":
        filters.append(Supplier.type == Supplier_Type(type_of))

    if search:
        filters.append(
            or_(
                Supplier.name.ilike(f"%{search}%"),
                Supplier.reason_name.ilike(f"%{search}%"),
                Supplier.document.ilike(f"%{search}%")
            )
        )

    total_supliers = db.query(Supplier).filter(Supplier.company_id == company_id).count()

    suppliers_data = db.query(Supplier).filter(*filters).order_by(
        desc(Supplier.date)
    ).limit(limit).offset(offset).all()

    for supplier in suppliers_data:
        suppliers.append({
            "id": supplier.id,
            "name": supplier.name,
            "reason_name": supplier.reason_name,
            "document": supplier.document,
            "type": supplier.type,
            "is_active": supplier.is_active
        })

    return custom_response(status_code=200, message=translate(lang, "company.suppliers.create.success"), data={
        "suppliers": suppliers,
        "pagination": pagination(total_supliers, limit, offset)
    })


########## Create Supplier ##########
@router.post("/create")
async def create_supplier(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.suppliers.create", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Get Body ###
    supplier_check, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(supplier_check, [
        "name", "reason_name", "document", "email", "phone", "address", "supplier_type", "is_active"
    ])

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    if not supplier_check.supplier_type in Supplier_Type._value2member_map_:
        return custom_response(status_code=400, message=translate(lang, "company.suppliers.create.error.incorrect_type"))

    # Create Supplier
    new_supplier = Supplier(
        id = get_uuid(db, Supplier),
        name = supplier_check.name,
        type = Supplier_Type(supplier_check.supplier_type),

        company_id = company_id
    )

    reason_name = supplier_check.reason_name
    document = supplier_check.document
    email = supplier_check.email
    phone = supplier_check.phone
    address = supplier_check.address
    domain = supplier_check.domain
    is_active = supplier_check.is_active

    if reason_name != "none":
        new_supplier.reason_name = reason_name

    if document != "none":
        new_supplier.document = document

    if email != "none":
        new_supplier.email = email

    if phone != "none":
        new_supplier.phone = phone

    if address != "none":
        new_supplier.address = address
    
    if domain != "none":
        new_supplier.domain = domain

    if is_active == "0":
        new_supplier.is_active = False

    add_db(db, new_supplier)

    return custom_response(status_code=200, message=translate(lang, "company.suppliers.create.success"), data={
        "supplier_id": new_supplier.id
    })
