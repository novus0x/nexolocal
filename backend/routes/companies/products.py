########## Modules ##########
import csv

from io import StringIO

from fastapi import APIRouter, Request, Depends, UploadFile, File

from sqlalchemy import func, desc, or_, case, asc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Company, Product, Product_Batch, Product_Service_Duration, Expense, Expense_Category, Expense_Status, Cash_Session_Status, Cash_Session, Cash_Movement_Type, Cash_Movement, Payment_Method, Supplier

from core.i18n import translate
from core.generator import get_uuid, get_uuid_value
from core.responses import custom_response
from core.permissions import check_permissions
from core.db_management import add_db, add_multiple_db, update_db
from core.validators import read_json_body, validate_required_fields
from core.utils import is_int, is_float, validate_not_same_day, pagination, normalize_search

########## Variables ##########
router = APIRouter()

########## Aux Functions ##########
def check_sku(db, sku_v, company_id):
    while (1):
        if db.query(Product).filter(
            Product.sku == sku_v,
            Product.company_id == company_id
            ).first():
            sku_v = get_uuid_value()
        else:
            break

    return sku_v

########## Get Products ##########
@router.get("/")
async def get_products(request: Request, page = 1, type_of = "all", q = None, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    products_data = []
    stock_value = 0
    low_threshold = 1.43

    ### Params ###
    page = is_int(page)

    if not page:
        page = 1

    limit = 12
    page = max(page, 1)
    offset = (page - 1) * limit

    if not type_of in ["all", "products", "services"]:
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
    access, message = check_permissions(db, request, "company.products.read", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Filter ###
    filters = [Product.company_id == company_id]

    urgency_expr = case(
        (
            (Product.low_stock_alert > 0) & (Product.stock >= 0),
            Product.stock / Product.low_stock_alert
        ),
        else_=999999
    )

    if type_of == "products":
        filters.append(Product.is_service == False)
    elif type_of == "services":
        filters.append(Product.is_service == True)

    if search:
        filters.append(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.identifier.ilike(f"%{search}%")
            )
        )

    ### DB request ###
    products = db.query(Product).filter(*filters).order_by(
        desc(Product.track_inventory),
        asc(urgency_expr),
        desc(Product.date)
    ).limit(limit).offset(offset).all()

    total_items = db.query(Product).filter(*filters).count()

    stock_value = (
        db.query(
            func.coalesce(func.sum(Product.stock * Product.cost), 0)
        )
        .filter(Product.company_id == company_id)
        .scalar()
    )

    low_products_quantity = db.query(func.count(Product.id)).filter(*filters).filter(
        Product.track_inventory == True
    ).filter(urgency_expr < low_threshold).scalar()
    
    for product in products:
        revenue = product.price - product.cost
        bar_status = "full" # medium low

        product_val = {
            "id": product.id,
            "identifier": product.identifier,
            "sku": product.sku,
            "name": product.name,
            "price": product.price,
            "cost": product.cost,
            "revenue": revenue,
            "stock": product.stock,
            "track_inventory": product.track_inventory,
            "is_service": product.is_service
        }

        if product.track_inventory:
            stock_value = product.stock

            if stock_value > 0:
                bar = 100
            
                d = (100 / product.stock) * product.low_stock_alert
                bar -= d
            
            else:
                bar = 0

            if bar >= 65: bar_status = "full"
            elif bar >= 30: bar_status = "medium"
            else: 
                bar_status = "low"

            product_val["bar_percentage"] = bar
            product_val["bar_status"] = bar_status

        products_data.append(product_val)

    return custom_response(status_code=200, message=translate(lang, "company.products.get.success"), data={
        "items_quantity": total_items,
        "stock_value": stock_value,
        "low_products_quantity": low_products_quantity,
        "products": products_data,
        "pagination": pagination(total_items, limit, offset)
    })

########## Create Product - GET ##########
@router.get("/create")
async def create_product_data(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    suppliers = []
        
    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "company.products.read", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Filter ###
    filters = [Supplier.company_id == company_id]

    suppliers_data = db.query(Supplier).filter(*filters).order_by(
        desc(Supplier.date)
    ).all()

    for supplier in suppliers_data:
        suppliers.append({
            "id": supplier.id,
            "name": supplier.name
        })

    return custom_response(status_code=200, message=translate(lang, "company.products.get.success"), data={
        "suppliers": suppliers
    })

########## Create Product - POST ##########
@router.post("/create")
async def create_product(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.products.create", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Check Cash Session --> OPEN ###
    """cash_session = db.query(Cash_Session).filter(
        Cash_Session.status == Cash_Session_Status.OPEN,
        Cash_Session.company_id == company_id,
    ).first()

    if not cash_session:
        return custom_response(status_code=400, message=translate(lang, "validation.no_open_cash_session"))
    """

    ### Get Body ###
    product_check, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(product_check, [
        "name", "sku", "identifier", "category", "description", "supplier_id", "sale_price", "sale_cost", "tax_include", 
        "is_bulk", "is_service", "duration", "duration_type", "staff_id", "track_product", "low_stock", "bonus", "weight",
        "length", "width", "height", "expiration_date"
    ])

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    bonus = is_float(product_check.bonus)
    stock = is_float(product_check.stock)
    cost = is_float(product_check.sale_cost)
    price = is_float(product_check.sale_price)

    if price is None or cost is None or stock is None:
        return custom_response(status_code=400, message=translate(lang, "company.products.create.error.incorrect_price"))
    
    if price <= 0 or cost < 0 or stock < 0:
        return custom_response(status_code=400, message=translate(lang, "company.products.create.error.incorrect_price"))

    if price < cost:
        return custom_response(status_code=400, message=translate(lang, "company.products.create.inconsistent_price_comparation"), details=required_fields)

    is_bulk = product_check.is_bulk
    is_service = product_check.is_service

    if is_bulk == "1" and is_service == "1":
        return custom_response(status_code=400, message=translate(lang, "company.products.create.error.bulk_service_not_allowed"))

    if is_service == "1":
        if not product_check.duration_type in Product_Service_Duration._value2member_map_:
            return custom_response(status_code=400, message=translate(lang, "company.products.create.incorrect_servide_duration"))
    else:
        if not is_bulk == "1":
            if stock != is_int(stock):
                return custom_response(status_code=400, message=translate(lang, "company.products.create.error.bulk_service_not_allowed"))
            
            stock = is_int(stock)

    if bonus is None:
        bonus = 0
    
    if bonus < 0:
        return custom_response(status_code=400, message=translate(lang, "company.products.create.error.incorrect_quantity"))

    # Create Product
    new_product = Product(
        id = get_uuid(db, Product),
        identifier = product_check.identifier,
        name = product_check.name,
        description = product_check.description,
        price = price,
        cost = cost,
        stock = stock + bonus,
        weight = product_check.weight,
        dimensions = f"{product_check.length}x{product_check.width}x{product_check.height}",
        company_id = company_id,
    )

    sku_v = product_check.sku
    
    ## Check sku ##
    if not sku_v or sku_v == "0":
        sku_v = get_uuid_value()

    new_product.sku = check_sku(db, sku_v, company_id)

    ## Supplier ##
    if product_check.supplier_id != "none":
        print(product_check.supplier_id)
        check_supplier = db.query(Supplier).filter(
            Supplier.id == product_check.supplier_id
        ).first()

        if check_supplier:
            new_product.supplier_id = check_supplier.id

            print(new_product.supplier_id)

    ## Track Inventory ##
    if product_check.track_product == "1":
        low_stock = is_float(product_check.low_stock)

        if low_stock is None or low_stock < 0:
            return custom_response(status_code=400, message=translate(lang, "company.products.create.error.incorrect_quantity"))

        new_product.track_inventory = True
        new_product.low_stock_alert = low_stock

    ## Bulk ##
    if is_bulk == "1":
        new_product.weight = 0
        new_product.is_bulk = True
        new_product.dimensions = "0x0x0"

    ## Service ##
    if is_service == "1":
        new_product.is_service = True
        new_product.duration_type = Product_Service_Duration(product_check.duration_type)
        new_product.duration = product_check.duration
        new_product.track_inventory = False

        if product_check.staff_id != "0":
            print("check staff id")

    ## Check Company Status - Taxes
    check_company = db.query(Company).filter(Company.id == company_id).first()

    if check_company.is_formal:
        print("To-do: implement taxes part I")

        if product_check.tax_include == "1":
            new_product.tax_included = True

    add_db(db, new_product)

    ## Create Product Batch
    new_product_batch = None

    if new_product.stock > 0:
        new_product_batch = Product_Batch(
            id = get_uuid(db, Product_Batch),
            stock = new_product.stock,
            stock_bonus = bonus,
            price = new_product.price,
            cost = new_product.cost,
            product_id = new_product.id
        )

        exp = validate_not_same_day(product_check.expiration_date)

        if exp:
            new_product_batch.expiration_date = exp,
        else:
            new_product_batch.expiration_active = False

    ## Create Expense ##
    if new_product_batch and new_product.cost > 0:
        # Create Expense
        amount_v = stock * new_product.cost

        new_expense = Expense(
            id = get_uuid(db, Expense),
            name = f"Nueva Compra: {new_product.name}",
            amount = amount_v,
            total_amount = amount_v,

            category = Expense_Category.SUPPLIES,
            status = Expense_Status.PAID,
            approved_by_id = user.get("id"),
            company_id = company_id
        )

        if check_company.is_formal:
            print("To-do: implement taxes part II")
            if product_check.tax_include == "1":
                new_expense.tax_amount = 0

        add_db(db, new_expense)
        """
        new_cash_movement = Cash_Movement(
            id = get_uuid(db, Cash_Movement),
            type = Cash_Movement_Type.EXPENSE,
            amount = new_expense.total_amount,
            payment_method = Payment_Method.CASH,

            related_expense_id = new_expense.id,

            cash_session_id = cash_session.id,
            company_id = company_id
        )

        add_db(db, new_cash_movement)
        """

        new_product_batch.expense_id = new_expense.id
    
    if new_product_batch:
        add_db(db, new_product_batch)

    return custom_response(status_code=200, message=translate(lang, "company.products.create.success"), data={
        "product_id": new_product.id
    })

########## Import Products ##########
@router.post("/import")
async def import_products(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id
    
    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.products.import.csv", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Check Cash Session --> OPEN ###
    """
    cash_session = db.query(Cash_Session).filter(
        Cash_Session.status == Cash_Session_Status.OPEN,
        Cash_Session.company_id == company_id,
    ).first()

    if not cash_session:
        return custom_response(status_code=400, message=translate(lang, "validation.no_open_cash_session"))
    """

    ### Check Valid File ###
    if not file.filename.lower().endswith(".csv"):
        return custom_response(status_code=400, message=translate(lang, "validation.invalid_file_type"))

    contents = await file.read()

    text = contents.decode("utf-8")
    reader = csv.DictReader(StringIO(text))
    headers = reader.fieldnames or []

    REQUIRED_HEADERS = {"identifier", "name", "price", "cost", "stock"}

    if not REQUIRED_HEADERS.issubset(set(headers)):
        return custom_response(status_code=400, message=translate(lang, "company.products.import.invalid_headers"))

    ### Products ###
    products = []
    uids_in_use = []
    products_no_created = 0
    
    for i, row in enumerate(reader):
        product_id = get_uuid(db, Product)

        while product_id in uids_in_use:
            product_id = get_uuid(db, Product)

        uids_in_use.append(product_id)

        if not row.get("identifier"):
            products_no_created += 1
            continue

        check_product = db.query(Product).filter(
            Product.identifier == row.get("identifier"),
            Product.company_id == company_id
        ).first()

        if check_product:
            products_no_created += 1
            continue

        if not row.get("name"):
            products_no_created += 1
            continue
        
        ## Parse Numbers ##
        price = is_float(row.get("price"))
        cost = is_float(row.get("cost"))
        stock = is_float(row.get("stock"))

        if price is None or cost is None or stock is None:
            products_no_created += 1
            continue
        
        if price <= 0 or cost < 0 or stock < 0:
            products_no_created += 1
            continue

        if cost > price:
            products_no_created += 1
            continue

        ## Check if is a bulk product ##
        is_bulk = row.get("is_bulk")

        if is_bulk != 1:
            if stock % 1 != 0:
                products_no_created += 1
                continue
        
        ## Create Product ##
        product = Product(
            id = product_id,
            identifier = row.get("identifier"),
            name = row.get("name"),
            price = price,
            cost = cost,
            stock = stock,
            company_id = company_id,
        )
        
        if is_bulk == "1":
            product.is_bulk = True
        
        ## SKU ###
        sku_v = row.get("sku")

        if sku_v:
            if sku_v == "0":
                sku_v = get_uuid_value()
        
        else:
            sku_v = get_uuid_value()
        
        product.sku = check_sku(db, sku_v, company_id)

        ## Optional Fields ##
        if row.get("description"):
            product.description = row.get("description")

        if row.get("track_inventory") == "1":
            low_stock = is_float(row.get("low_stock_alert"))

            if low_stock is not None and low_stock >= 0:
                product.track_inventory = True
                product.low_stock_alert = low_stock

        if row.get("weight"):
            w = is_float(row.get("weight"))
            if w is not None and w >= 0:
                product.weight = w

        if row.get("dimensions"):
            product.dimensions = row.get("dimensions")

        if row.get("is_service") == "1":
            if row.get("duration") and row.get("duration_type") in Product_Service_Duration._value2member_map_:
                product.is_service = True
                product.duration = row.get("duration")
                product.duration_type = Product_Service_Duration(row.get("duration_type"))
                product.track_inventory = False
        
        products.append(product)

    ### Product Batchs ###
    product_batchs = []
    uids_bath_in_use = []

    expenses = []
    uids_expenses_in_use = []

    new_cash_movements = []
    uids_new_cash_movement_in_use = []

    for product in products:
        if product.stock <= 0:
            continue

        product_batch_id = get_uuid(db, Product_Batch)

        while product_batch_id in uids_in_use:
            product_batch_id = get_uuid(db, Product_Batch)

        uids_bath_in_use.append(product_batch_id)

        ## Create Batch ##
        product_batch = Product_Batch(
            id = product_batch_id,
            stock = product.stock,
            price = product.price,
            cost = product.cost,
            product_id = product.id,
            # expense_id = new_expense.id,
            expiration_active = False
        )

        if product.cost > 0:
            expense_id = get_uuid(db, Expense)
            new_cash_movement_id = get_uuid(db, Cash_Movement)

            while expense_id in uids_expenses_in_use:
                expense_id = get_uuid(db, Expense)

            while new_cash_movement_id in uids_new_cash_movement_in_use:
                new_cash_movement_id = get_uuid(db, Cash_Movement)

            uids_expenses_in_use.append(expense_id)
            uids_new_cash_movement_in_use.append(new_cash_movement_id)
            
            amount_v = product.stock * product.cost

            new_expense = Expense(
                id = expense_id,
                name = f"Nueva Compra: {product.name}",
                amount = amount_v,
                total_amount = amount_v,

                category = Expense_Category.SUPPLIES,
                status = Expense_Status.PAID,
                approved_by_id = user.get("id"),
                company_id = company_id
            )

            """
            new_cash_movement = Cash_Movement(
                id = new_cash_movement_id,
                type = Cash_Movement_Type.EXPENSE,
                amount = new_expense.total_amount,
                payment_method = Payment_Method.CASH,

                related_expense_id = new_expense.id,

                cash_session_id = cash_session.id,
                company_id = company_id
            )
            """

            product_batch.expense_id = new_expense.id

            expenses.append(new_expense)
            # new_cash_movements.append(new_cash_movement)
        
        product_batchs.append(product_batch)

    add_multiple_db(db, products)
    add_multiple_db(db, expenses)
    add_multiple_db(db, product_batchs)
    # add_multiple_db(db, new_cash_movements)

    return custom_response(status_code=200, message=translate(lang, "company.products.import.success"), data={
        "products_no_created": products_no_created
    })

########## Get Product ##########
@router.get("/get/{product_id}")
async def get_product_by_id(request: Request, product_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    supplier = {}
    product_batchs_values = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "company.products.read", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    if not product_id:
        return custom_response(status_code=400, message=translate(lang, "company.products.get.single.error"))
    
    check_product = db.query(Product).filter(
        Product.id == product_id,
        company_id == company_id
    ).first()

    if not check_product:
        return custom_response(status_code=400, message=translate(lang, "company.products.get.single.error"))
    
    supplier = db.query(Supplier).filter(
        Supplier.id == check_product.supplier_id
    ).first()

    print(check_product.supplier_id)

    if supplier:
        supplier ={
            "id": supplier.id,
            "name": supplier.name,
            "reason_name": supplier.reason_name,
            "document": supplier.document
        }

    product_batchs = (
        db.query(
            Product_Batch.id.label("id"),
            Product_Batch.stock.label("stock"),
            Product_Batch.is_active.label("is_active"),
            Product_Batch.expiration_active.label("expiration_active"),
            Product_Batch.expiration_date.label("expiration_date"),
            Product_Batch.date.label("date")
        ).filter(
            Product_Batch.product_id == check_product.id,
        ).order_by(desc(Product_Batch.date)).limit(8).all()
    )

    for batch in product_batchs:
        batch_value = {
            "id": batch.id,
            "stock": batch.stock,
            "is_active": batch.is_active,
            "expiration_date": batch.expiration_date.astimezone().strftime("%d %b %Y"),
            "date": batch.date.astimezone().strftime("%H:%M - %d %b %Y")
        }

        product_batchs_values.append(batch_value)

    print(supplier)

    return custom_response(status_code=200, message=translate(lang, "company.products.get.single.success"), data={
        "product": check_product,
        "supplier": supplier,
        "batchs": product_batchs_values
    })

########## Get Product - Batch Section ##########
@router.get("/{product_id}/batchs/create")
async def get_product_by_id_to_create_batch(request: Request, product_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.products.read", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    if not product_id:
        return custom_response(status_code=400, message=translate(lang, "company.products.get.single.error"))

    check_product = db.query(Product).filter(
        Product.id == product_id,
        company_id == company_id
    ).first()

    if not check_product:
        return custom_response(status_code=400, message=translate(lang, "company.products.get.single.error"))
    
    product = {
        "id": check_product.id,
        "sku": check_product.sku,
        "identifier": check_product.identifier,
        "stock": check_product.stock,
        
        "name": check_product.name,
        "description": check_product.description,
        "price": check_product.price,
        "cost": check_product.cost,

        "tax_included": check_product.tax_included,
        "low_stock_alert": check_product.low_stock_alert,
        "track_inventory": check_product.track_inventory,

        "is_bulk": check_product.is_bulk,

        "is_service": check_product.is_service,
        "duration": check_product.duration,

        "is_active": check_product.is_active,
        "is_visible": check_product.is_visible
    }
    
    return custom_response(status_code=200, message=translate(lang, "company.products.get.single.success"), data={
        "product": product,
    })

########## Create Batch - Batch Section ##########
@router.post("/{product_id}/batchs/create")
async def add_new_batch(request: Request, product_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.products.create", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Check Cash Session --> OPEN ###
    """
    cash_session = db.query(Cash_Session).filter(
        Cash_Session.status == Cash_Session_Status.OPEN,
        Cash_Session.company_id == company_id,
    ).first()

    if not cash_session:
        return custom_response(status_code=400, message=translate(lang, "validation.no_open_cash_session"))
    """

    ### Get Body ###
    product_check, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(product_check, [
        "product_id", "quantity", "bonus", "price", "cost", "reception_date", "expiration_date"
    ])

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    ## Parse Numbers ##
    price = is_float(product_check.price)
    cost = is_float(product_check.cost)
    stock = is_float(product_check.quantity)
    bonus = is_float(product_check.bonus) or 0

    if stock is None or bonus is None or price is None or cost is None:
        return custom_response(status_code=400, message=translate(lang, "company.products.create.batch.error"))

    if stock < 0 or bonus < 0 or price <= 0 or cost < 0:
        return custom_response(status_code=400, message=translate(lang, "company.products.create.batch.error"))

    ## Get Product ##
    product = db.query(Product).filter(
        Product.id == product_check.product_id,
        Product.company_id == company_id
    ).first()

    if not product:
        return custom_response(status_code=400, message=translate(lang, "company.products.create.batch.error"))

    if not product.is_bulk:
        if stock % 1 != 0 or bonus % 1 != 0:
            return custom_response(status_code=400, message=translate(lang, "company.products.create.batch.error"))

    ## Create Batch ##
    new_batch = Product_Batch(
        id = get_uuid(db, Product_Batch),
        stock = stock + bonus,
        stock_bonus = bonus,
        price = price,
        cost = cost,
        product_id = product.id
    )

    exp = validate_not_same_day(product_check.expiration_date)

    if exp:
        new_batch.expiration_date = exp
    else:
        new_batch.expiration_active = False

    rcd = validate_not_same_day(product_check.reception_date)

    if rcd:
        new_batch.date = rcd

    ## Update Product Values ##
    product.stock += new_batch.stock

    if price != product.price:
        product.price = price
    
    if cost != product.cost:
        product.cost = cost
    
    ## Create Expense ##
    if cost > 0:
        amount_v = stock * new_batch.cost

        company = db.query(Company).filter(
            Company.id == company_id
        ).first()

        new_expense = Expense(
            id = get_uuid(db, Expense),
            name = f"Nueva Compra de Lote: {product.name}",
            amount = amount_v,
            total_amount = amount_v,

            category = Expense_Category.SUPPLIES,
            status = Expense_Status.PAID,
            approved_by_id = user.get("id"),
            company_id = company_id
        )

        if company.is_formal:
            print("To-do: implement taxes part II")
            if product_check.tax_include == "1":
                new_expense.tax_amount = 0

        new_batch.expense_id = new_expense.id

        """
        new_cash_movement = Cash_Movement(
            id = get_uuid(db, Cash_Movement),
            type = Cash_Movement_Type.EXPENSE,
            amount = new_expense.total_amount,
            payment_method = Payment_Method.CASH,

            related_expense_id = new_expense.id,
            
            company_id = company_id,
            cash_session_id = cash_session.id
        )
        """

        add_db(db, new_expense)
        # add_db(db, new_cash_movement)

    update_db(db)
    add_db(db, new_batch)

    return custom_response(status_code=200, message=translate(lang, "company.products.create.batch.success"), data={})
