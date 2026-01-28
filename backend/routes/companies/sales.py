########## Modules ##########
from datetime import datetime, timedelta, date, time

from fastapi import APIRouter, Request, Depends

from sqlalchemy import or_, desc, func, extract
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Product, Product_Batch, Company, Payment_Method, Sale, Sale_Item, Sale_Status, Income, Income_Status, User, Cash_Session_Status, Cash_Session, Cash_Movement_Type, Cash_Movement, Expense, Expense_Status

from core.i18n import translate
from core.generator import get_uuid, generate_nxid
from core.utils import is_int, pagination, normalize_search
from core.responses import custom_response
from core.permissions import check_permissions
from core.db_management import add_db, update_db, add_multiple_db
from core.validators import read_json_body, validate_required_fields

########## Variables ##########
router = APIRouter()

########## Check Sale - Company ##########
@router.get("/")
async def check_product_scan(request: Request, page = 1, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    sales_data = []

    ### Pagination ###
    page = is_int(page)

    if not page:
        page = 1

    limit = 10
    page = max(page, 1)
    offset = (page - 1) * limit

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    if not check_permissions(db, request, "company.sales.read", company_id):
        return custom_response(status_code=400, message=translate(lang, "validation.not_necessary_permission"))
    
    sales = db.query(Sale).filter(
        Sale.company_id == company_id
    ).order_by(
        desc(Sale.date)
    ).limit(limit).offset(offset).all()

    for sale in sales:
        sales_data.append({
            "id": sale.id,
            "invoice": sale.invoice_number,
            "amount": sale.total,

            "client": {},
            "date": sale.date.astimezone().strftime("%H:%M - %d %b %Y"),
        })

    return custom_response(status_code=200, message=translate(lang, "company.sales.get.success"), data={
        "sales": sales_data
    })

########## Cash Flow - Company - API ##########
@router.post("/flow")
async def check_product_scan(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    available_options = ["today", "7d", "30d", "6m", "12m"]

    now = datetime.now()
    today = date.today()

    labels = []
    income_map = {}
    expense_map = {}

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    if not check_permissions(db, request, "company.sales.create", company_id):
        return custom_response(status_code=400, message=translate(lang, "validation.not_necessary_permission"))

    ### Get Body ###
    check_flow, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(check_flow, [
        "type"
    ])

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    if not check_flow.type in available_options:
        return custom_response(status_code=200, message=translate(lang, "company.sales.flow.error.incorrect_option"))

    if check_flow.type == "today":
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)
        mode = "hour"

    elif check_flow.type == "7d":
        start = datetime.combine(today - timedelta(days=6), time.min)
        end = now
        mode = "day"

    elif check_flow.type == "30d":
        start = datetime.combine(today - timedelta(days=29), time.min)
        end = now
        mode = "day"

    elif check_flow.type == "6m":
        base = today.replace(day=1) - timedelta(days=180)
        start = datetime.combine(base.replace(day=1), time.min)
        end = now
        mode = "month"

    elif check_flow.type == "12m":
        base = today.replace(day=1) - timedelta(days=365)
        start = datetime.combine(base.replace(day=1), time.min)
        end = now
        mode = "month"

    if mode == "hour":
        for h in range(0, 24):
            key = f"{h:02d}:00"
            labels.append(key)
            income_map[key] = 0
            expense_map[key] = 0
    
    if mode == "day":
        d = start.date()

        while d <= end.date():
            key = d.strftime("%d %b")
            labels.append(key)
            income_map[key] = 0
            expense_map[key] = 0
            d += timedelta(days=1)

    if mode == "month":
        d = start.replace(day=1)
        
        while d <= end:
            key = d.strftime("%b %Y")
            labels.append(key)
            income_map[key] = 0
            expense_map[key] = 0
            if d.month == 12:
                d = d.replace(year=d.year+1, month=1)
            else:
                d = d.replace(month=d.month+1)

    if mode == "hour":
        rows = db.query(
            extract("hour", Cash_Movement.date),
            func.coalesce(func.sum(Cash_Movement.amount), 0)
        ).filter(
            Cash_Movement.company_id == company_id,
            Cash_Movement.type.in_([
                Cash_Movement_Type.SALE,
                Cash_Movement_Type.INCOME
            ]),
            Cash_Movement.date >= start,
            Cash_Movement.date <= end
        ).group_by(extract("hour", Cash_Movement.date)).all()

        for h, total in rows:
            key = f"{int(h):02d}:00"
            income_map[key] = float(total)

    elif mode == "day":
        rows = db.query(
            func.date(Cash_Movement.date),
            func.coalesce(func.sum(Cash_Movement.amount), 0)
        ).filter(
            Cash_Movement.company_id == company_id,
            Cash_Movement.type.in_([
                Cash_Movement_Type.SALE,
                Cash_Movement_Type.INCOME
            ]),
            Cash_Movement.date >= start,
            Cash_Movement.date <= end
        ).group_by(func.date(Cash_Movement.date)).all()

        for d, total in rows:
            key = d.strftime("%d %b")
            income_map[key] = float(total)

    elif mode == "month":
        rows = db.query(
            extract("year", Cash_Movement.date),
            extract("month", Cash_Movement.date),
            func.coalesce(func.sum(Cash_Movement.amount), 0)
        ).filter(
            Cash_Movement.company_id == company_id,
            Cash_Movement.type.in_([
                Cash_Movement_Type.SALE,
                Cash_Movement_Type.INCOME
            ]),
            Cash_Movement.date >= start,
            Cash_Movement.date <= end
        ).group_by(
            extract("year", Cash_Movement.date),
            extract("month", Cash_Movement.date)
        ).all()

        for y, m, total in rows:
            key = datetime(int(y), int(m), 1).strftime("%b %Y")
            income_map[key] = float(total)

    if mode == "hour":
        rows = db.query(
            extract("hour", Cash_Movement.date),
            func.coalesce(func.sum(Cash_Movement.amount), 0)
        ).filter(
            Cash_Movement.company_id == company_id,
            Cash_Movement.type.in_([
                Cash_Movement_Type.EXPENSE,
                Cash_Movement_Type.WITHDRAW
            ]),
            Cash_Movement.date >= start,
            Cash_Movement.date <= end
        ).group_by(extract("hour", Cash_Movement.date)).all()

        for h, total in rows:
            key = f"{int(h):02d}:00"
            expense_map[key] = float(total)

    elif mode == "day":
        rows = db.query(
            func.date(Cash_Movement.date),
            func.coalesce(func.sum(Cash_Movement.amount), 0)
        ).filter(
            Cash_Movement.company_id == company_id,
            Cash_Movement.type.in_([
                Cash_Movement_Type.EXPENSE,
                Cash_Movement_Type.WITHDRAW
            ]),
            Cash_Movement.date >= start,
            Cash_Movement.date <= end
        ).group_by(func.date(Cash_Movement.date)).all()

        for d, total in rows:
            key = d.strftime("%d %b")
            expense_map[key] = float(total)

    elif mode == "month":
        rows = db.query(
            extract("year", Cash_Movement.date),
            extract("month", Cash_Movement.date),
            func.coalesce(func.sum(Cash_Movement.amount), 0)
        ).filter(
            Cash_Movement.company_id == company_id,
            Cash_Movement.type.in_([
                Cash_Movement_Type.EXPENSE,
                Cash_Movement_Type.WITHDRAW
            ]),
            Cash_Movement.date >= start,
            Cash_Movement.date <= end
        ).group_by(
            extract("year", Cash_Movement.date),
            extract("month", Cash_Movement.date)
        ).all()

        for y, m, total in rows:
            key = datetime(int(y), int(m), 1).strftime("%b %Y")
            expense_map[key] = float(total)

    income_data = [round(income_map[l], 2) for l in labels]
    expense_data = [round(expense_map[l], 2) for l in labels]

    return custom_response(status_code=200, message=translate(lang, "company.sales.flow.success"), data={
        "labels": labels,
        "sales": income_data,
        "expenses": expense_data
    })

########## Check Reports - Company ##########
@router.get("/reports")
async def check_product_scan(request: Request, page = 1, q = None, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    sales_data = []

    ### Pagination ###
    page = is_int(page)

    if not page:
        page = 1

    limit = 9
    page = max(page, 1)
    offset = (page - 1) * limit

    ### Search ###
    if q:
        q = q.strip()
        
        if len(q) < 2:
            q = None

    search = normalize_search(q)

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    if not check_permissions(db, request, "company.sales.read", company_id):
        return custom_response(status_code=400, message=translate(lang, "validation.not_necessary_permission"))
    
    ### DB Operation ###
    filters = [Sale.company_id == company_id]

    if search:
        filters.append(
            or_(
                Sale.id.ilike(f"%{search}%"),
                Sale.invoice_number.ilike(f"%{search}%"),
            )
        )

    sales = db.query(Sale).filter(*filters).order_by(
        desc(Sale.date)
    ).limit(limit).offset(offset).all()

    total_items = db.query(Sale).filter(*filters).count()

    for sale in sales:
        sales_data.append({
            "id": sale.id,
            "invoice": sale.invoice_number,
            "amount": sale.total,

            "client": {},
            "date": sale.date.astimezone().strftime("%H:%M - %d %b %Y"),
        })

    return custom_response(status_code=200, message=translate(lang, "company.sales.get.success"), data={
        "sales": sales_data,
        "pagination": pagination(total_items, limit, offset)
    })

########## Check Product - Scan - Company ##########
@router.post("/check_product_scan")
async def check_product_scan(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    if not check_permissions(db, request, "company.sales.create", company_id):
        return custom_response(status_code=400, message=translate(lang, "validation.not_necessary_permission"))

    ### Get Body ###
    check_product, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(check_product, [
        "identifier"
    ])

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    product = db.query(Product).filter(
        Product.identifier == check_product.identifier,
        Product.company_id == company_id
    ).first()

    if not product:
        return custom_response(status_code=400, message=translate(lang, "company.sales.check.error"))

    product_data = {
        "id": product.id,
        "identifier": product.identifier,
        "sku": product.sku,
        "name": product.name,
        "stock": product.stock,
        "price": product.price,
        "is_service": product.is_service
    }
    
    return custom_response(status_code=200, message=translate(lang, "company.sales.check.success"), data={
        "product": product_data
    })

########## Check Product - Search - Company ##########
@router.post("/check_product_search")
async def check_product_search(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    products_data = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    if not check_permissions(db, request, "company.sales.create", company_id):
        return custom_response(status_code=400, message=translate(lang, "validation.not_necessary_permission"))

    ### Get Body ###
    check_product, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(check_product, [
        "query"
    ])

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    query = check_product.query

    products = db.query(Product).filter(
        or_(
            Product.name.ilike(f"%{query}%"),
            Product.identifier.ilike(f"%{query}%")
        ),
        Product.company_id == company_id
    ).limit(10).all()

    for product in products:
        products_data.append({
            "id": product.id,
            "identifier": product.identifier,
            "sku": product.sku,
            "name": product.name,
            "stock": product.stock,
            "price": product.price,
            "is_service": product.is_service
        })
    
    return custom_response(status_code=200, message=translate(lang, "company.sales.check.success"), data={
        "products": products_data
    })

########## Create New Sale - Company ##########
@router.post("/create")
async def create_new_sale(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    products_data = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    if not check_permissions(db, request, "company.sales.create", company_id):
        return custom_response(status_code=400, message=translate(lang, "validation.not_necessary_permission"))

    ### Check Cash Session --> OPEN ###
    cash_session = db.query(Cash_Session).filter(
        Cash_Session.status == Cash_Session_Status.OPEN,
        Cash_Session.company_id == company_id,
    ).first()

    if not cash_session:
        return custom_response(status_code=400, message=translate(lang, "validation.no_open_cash_session"))

    ### Get Body ###
    check_sale, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(check_sale, [
        "client_id", "payment_method", "items"
    ])

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    client_id_data = check_sale.client_id # To-Do
    products_data = check_sale.items
    payment_method_value = check_sale.payment_method

    if not payment_method_value in Payment_Method._value2member_map_:
        return custom_response(status_code=400, message=translate(lang, "company.sales.create.error.incorrect_payment_method"))

    amount = 0
    sale_items = []
    sale_items_ids = []

    invoice_number = generate_nxid("sale")

    while db.query(Sale).filter(
        Sale.invoice_number == invoice_number
    ).first():
        invoice_number = generate_nxid("sale")

    new_sale = Sale(
        id = get_uuid(db, Sale),
        invoice_number = invoice_number,
        status = Sale_Status.COMPLETED,
        payment_method = Payment_Method(payment_method_value),
        company_id = company_id,
        seller_user_id = user.get("id")
    )

    for product in products_data:
        current_amount = 0
        quantity = is_int(product.get("qty"))

        if not quantity:
            return custom_response(status_code=400, message=translate(lang, "company.sales.create.error.incorrect_product_quantity"))

        check_product = db.query(Product).filter(
            Product.id == product.get("id"),
            Product.identifier == product.get("identifier"),
            Product.company_id == company_id
        ).first()

        if not check_product:
            return custom_response(status_code=400, message=translate(lang, "company.sales.create.error.product_does_not_exist"))

        if not check_product.is_service:
            batches = (
                db.query(Product_Batch)
                .filter(
                    Product_Batch.product_id == check_product.id,
                    Product_Batch.stock > 0
                )
                .order_by(Product_Batch.date.desc())
                .all()
            )

            remaining_qty = quantity

            if not batches:
                return custom_response(status_code=400, message=translate(lang, "company.sales.create.error.incorrect_product_quantity"))

            for batch in batches:
                if remaining_qty <= 0:
                    break

                take = min(batch.stock, remaining_qty)

                batch.stock -= take
                remaining_qty -= take

            if remaining_qty > 0:
                return custom_response(status_code=400, message=translate(lang, "company.sales.create.error.incorrect_product_quantity"))

        current_amount = check_product.price * quantity

        sale_item_id = get_uuid(db, Sale_Item)

        while sale_item_id in sale_items_ids:
            sale_item_id = get_uuid(db, Sale_Item)

        new_sale_item = Sale_Item(
            id = sale_item_id,
            sale_id = new_sale.id,
            product_id = check_product.id,

            name = check_product.name,
            quantity = quantity,
            unit_price = check_product.price,
            total = current_amount,
            is_service = check_product.is_service
        )

        amount += current_amount
        sale_items.append(new_sale_item)

        if not check_product.is_service:
            check_product.stock = check_product.stock - quantity

    new_income = Income(
        id = get_uuid(db, Income),
        name = "Nueva Venta",
        amount = amount,
        status = Income_Status.RECEIVED,
        approved_by_id = user.get("id"),
        company_id = company_id
    )

    new_sale.total = amount
    new_sale.subtotal = amount
    new_sale.income_id = new_income.id

    new_cash_movement = Cash_Movement(
        id = get_uuid(db, Cash_Movement),
        type = Cash_Movement_Type.SALE,
        amount = new_sale.total,
        payment_method = Payment_Method(new_sale.payment_method),

        related_sale_id = new_sale.id,

        company_id = company_id,
        cash_session_id = cash_session.id
    )

    update_db(db)
    add_db(db, new_income)
    add_db(db, new_sale)
    add_db(db, new_cash_movement)
    add_multiple_db(db, sale_items)
    
    return custom_response(status_code=200, message=translate(lang, "company.sales.create.success"), data={
        "sale_id": new_sale.id
    })

########## Check Sale Item - Company ##########
@router.get("/check_sale/{sale_id}")
async def check_product_scan(request: Request, sale_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    items = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    if not check_permissions(db, request, "company.sales.create", company_id):
        return custom_response(status_code=400, message=translate(lang, "validation.not_necessary_permission"))

    sale = db.query(Sale).filter(
        Sale.id == sale_id
    ).first()

    if not sale:
        return custom_response(status_code=400, message=translate(lang, "company.sales.check.error"))
    
    company = db.query(Company).filter(
        Company.id == sale.company_id
    ).first()

    if not Company:
        return custom_response(status_code=400, message=translate(lang, "company.sales.check.error"))
    
    seller = db.query(User).filter(
        User.id == sale.seller_user_id
    ).first()

    items_data = db.query(Sale_Item).filter(
        Sale_Item.sale_id == sale.id
    ).all()

    for item in items_data:
        product_value = {
            "name": item.name,
            "quantity": item.quantity,
            "price": item.unit_price,
            "total": item.total
        }

        items.append(product_value)

    company_information = {
        "name": company.name,
        "phone": company.phone,
        "address": company.address,

        "is_formal": company.is_formal,
    }

    sale_information = {
        "id": sale.id,
        "invoice": sale.invoice_number,
        "items": items,
        "tax": sale.tax_amount,
        "total": sale.total,
        "date": sale.date.astimezone().strftime("%H:%M - %d %b %Y"),

        "seller": {
            "name": seller.fullname
        }
    }
    
    return custom_response(status_code=200, message=translate(lang, "company.sales.check.success"), data={
        "company": company_information,
        "sale": sale_information
    })
