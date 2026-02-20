########## Modules ##########
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Request, Depends

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User_Role, Company_Plan

from core.config import settings

from core.i18n import translate
from core.generator import get_uuid
from core.utils import is_float, is_int
from core.responses import custom_response
from core.permissions import check_permissions
from core.db_management import add_db, update_db
from core.validators import read_json_body, validate_required_fields

########## Variables ##########
router = APIRouter()
TIMEZONE = settings.TIMEZONE

LOCAL_TZ = ZoneInfo(TIMEZONE)
UTZ_TZ = ZoneInfo("UTC")

########## Get Plans ##########
@router.get("/")
async def plans(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    plans = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.plans.read")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Get Plans ###
    plans_data = db.query(Company_Plan).order_by(asc(Company_Plan.position)).all()

    for plan in plans_data:
        descriptions_data = plan.description.split("\n")    

        plans.append({
            "id": plan.id,
            "name": plan.name,
            "price": plan.price,
            "description": descriptions_data,
            "highlight": plan.highlight,
            "highlight_title": plan.highlight_title,
            "highlight_subtitle": plan.highlight_subtitle,
            "cycle": plan.plan_cycle
        })
        
    return custom_response(status_code=200, message=translate(lang, "platform.plans.get.success"), data={
        "plans": plans
    })

########## Get roles to select - Create Plan ##########
@router.get("/get_roles")
async def roles_generate_company(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    roles = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.plans.create")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Operations ###
    filters = [
        User_Role.platform_level == True,
        User_Role.hidden == False
    ]

    roles_data = db.query(User_Role).filter(*filters).all()

    for role in roles_data:
        roles.append({
            "id": role.id,
            "name": role.name,
            "hidden": role.hidden
        })
        
    return custom_response(status_code=200, message=translate(lang, "platform.plans.get_roles"), data={
        "roles": roles
    })

########## Create Plan ##########
@router.post("/create")
async def create_plan(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.plans.create")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Get Body ###
    new_plan_data, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)
    
    ### Validations ###
    required_fields, error = validate_required_fields(new_plan_data, ["name", "price", "description", "highlight", "highlight_title", "highlight_subtitle", "cycle", "position", "role_id"], lang)
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    ### Validate Price & Position ###
    price = is_float(new_plan_data.price)
    position = is_int(new_plan_data.position)

    if not price:
        return custom_response(status_code=400, message=translate(lang, "platform.plans.create.error.invalid_price"))
    
    if position == None:
        return custom_response(status_code=400, message=translate(lang, "platform.plans.create.error.invalid_position"))
    elif position < 0:
        return custom_response(status_code=400, message=translate(lang, "platform.plans.create.error.invalid_position"))

    ### Check Role ###
    check_role = db.query(User_Role).filter(User_Role.id == new_plan_data.role_id).first()

    if not check_role:
        return custom_response(status_code=400, message=translate(lang, "platform.plans.create.error.invalid_role"))
    
    ### Validate Plan Position ###
    plans = db.query(Company_Plan).order_by(desc(Company_Plan.position)).all()

    q_plans = len(plans)

    ### Clamp Position ###
    if position > q_plans:
        position = q_plans

    ### Check if position is in use ###
    for plan in plans:

        if plan.position >= position:
            plan.position += 1

    ### Update if positions changes ###
    update_db(db)

    ### Create Plan ###
    new_plan = Company_Plan(
        id = get_uuid(db, Company_Plan),
        name = new_plan_data.name,
        price = price,
        description = new_plan_data.description,

        position = position,

        role_id = check_role.id
    )

    if new_plan_data.highlight == "1":
        new_plan.highlight = True
        new_plan.highlight_title = new_plan_data.highlight_title
        new_plan.highlight_subtitle = new_plan_data.highlight_subtitle

    ### Add to DB ###
    add_db(db, new_plan)

    return custom_response(status_code=200, message=translate(lang, "platform.plans.create.success"))

########## Get User by ID ##########
@router.get("/get/{plan_id}")
async def get_user_by_id(request: Request, plan_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    plan = {}

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.plans.read")
    
    if not access:
        return custom_response(status_code=400, message=message)

    ### Get Plan Info ###
    check_plan = db.query(Company_Plan).filter(
        Company_Plan.id == plan_id
    ).first()

    if not check_plan:
        return custom_response(status_code=400, message=translate(lang, "platform.plans.get.error"))
    
    plan = {
        "id": check_plan.id,
        "name": check_plan.name,
        "price": check_plan.price,
        "position": check_plan.position,
        "description": check_plan.description,
        "highlight": check_plan.highlight,
        "highlight_title": check_plan.highlight_title,
        "highlight_subtitle": check_plan.highlight_subtitle,
        "role_id": check_plan.role_id
    }

    return custom_response(status_code=200, message=translate(lang, "platform.plans.get.unique"), data={
        "plan": plan
    })

########## Update Plan ##########
@router.post("/update")
async def update_plan(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.plans.create")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Get Body ###
    edit_plan_data, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)
    
    ### Validations ###
    required_fields, error = validate_required_fields(edit_plan_data, ["plan_id", "name", "price", "description", "highlight", "highlight_title", "highlight_subtitle", "cycle", "position", "role_id"], lang)
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    ### Validate Plan ###
    check_plan = db.query(Company_Plan).filter(
        Company_Plan.id == edit_plan_data.plan_id
    ).first()

    if not check_plan:
        return custom_response(status_code=400, message=translate(lang, "platform.plans.update.error.general"))

    ### Validate Price & Position ###
    price = is_float(edit_plan_data.price)
    position = is_int(edit_plan_data.position)

    if not price:
        return custom_response(status_code=400, message=translate(lang, "platform.plans.update.error.invalid_price"))
    
    if position == None:
        return custom_response(status_code=400, message=translate(lang, "platform.plans.update.error.invalid_position"))
    elif position < 0:
        return custom_response(status_code=400, message=translate(lang, "platform.plans.update.error.invalid_position"))

    ### Check Role ###
    check_role = db.query(User_Role).filter(User_Role.id == edit_plan_data.role_id).first()

    if not check_role:
        return custom_response(status_code=400, message=translate(lang, "platform.plans.update.error.invalid_role"))
    
    if check_plan.position != position:
        ### Extra ###
        new_position = position
        old_position = check_plan.position

        ### Validate Plan Position ###
        plans = db.query(Company_Plan).filter(
            Company_Plan.id != check_plan.id
        ).order_by(desc(Company_Plan.position)).all()

        q_plans = len(plans)

        ### Clamp ###
        if new_position < 0:
            new_position = 0

        elif new_position > q_plans:
            new_position = q_plans

        ### Up ###
        if new_position < old_position:
            for plan in plans:
                if new_position <= plan.position < old_position:
                    plan.position += 1

        ### Down ###
        elif new_position > old_position:
            for plan in plans:
                if old_position < plan.position <= new_position:
                    plan.position -= 1

        ### Update Current Plan Position ###
        check_plan.position = new_position

    ### Update Plan ###
    check_plan.name = edit_plan_data.name
    check_plan.price = edit_plan_data.price
    check_plan.description = edit_plan_data.description
    # check_plan.role_id = edit_plan_data.role_id # need to fix this later

    if edit_plan_data.highlight:
        check_plan.highlight = True
        check_plan.highlight_title = edit_plan_data.highlight_title
        check_plan.highlight_subtitle = edit_plan_data.highlight_subtitle
    else:
        check_plan.highlight = False
        check_plan.highlight_title = None
        check_plan.highlight_subtitle = None
        
    ### Update DB ###
    update_db(db)

    return custom_response(status_code=200, message=translate(lang, "platform.plans.update.success"))
