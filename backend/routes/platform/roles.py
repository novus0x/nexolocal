########## Modules ##########
from fastapi import APIRouter, Request, Depends

from sqlalchemy import or_
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User_Role

from core.i18n import translate
from core.generator import get_uuid
from core.responses import custom_response
from core.db_management import add_db, update_db
from core.validators import read_json_body, validate_required_fields
from core.permissions import get_permissions, filter_existing_permissions, check_permissions

########## Variables ##########
router = APIRouter()

########## Get Roles - Dashboard ##########
@router.get("/")
async def roles_platform(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    roles = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.roles.read")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Operations ###
    filters = [
        User_Role.platform_level == True,
    ]

    role_access, _ = check_permissions(db, request, "platform.users.role")

    if role_access:
        filters = [
            or_(
                User_Role.platform_level.is_(True),
                User_Role.hidden.is_(True)
            )
        ]

    roles_data = db.query(User_Role).filter(*filters).all()

    for role in roles_data:
        roles.append({
            "id": role.id,
            "name": role.name,
            "platform": role.platform_level,
            "date": role.date.strftime("%d %B %Y")
        })
        
    return custom_response(status_code=200, message=translate(lang, "platform.roles.get.success"), data={
        "roles": roles
    })

########## Get Permissions - Create Role ##########
@router.get("/get-permissions")
async def get_roles(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    permissions = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.roles.create")
    
    if not access:
        return custom_response(status_code=400, message=message)

    ### Operations ###
    permissions = get_permissions()
        
    return custom_response(status_code=200, message=translate(lang, "platform.roles.get.success"), data={
        "permissions": permissions
    })

########## Create Role - POST ##########
@router.post("/create")
async def create_role(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.roles.create")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Get Body ###
    new_role_data, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)
        
    required_fields, error = validate_required_fields(new_role_data, ["permissions", "role_name", "description", "hidden"])
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
        
    permissions = filter_existing_permissions(new_role_data.permissions)

    new_role = User_Role(
        id = get_uuid(db, User_Role),
        name = new_role_data.role_name,
        description = new_role_data.description,
        permissions = permissions,
        platform_level = True
    )

    if new_role_data.hidden == "1":
        new_role.hidden = True

    add_db(db, new_role)
        
    return custom_response(status_code=200, message=translate(lang, "platform.roles.create.success"), data={
        "role_id": new_role.id
    })

########## Get Role - To Update Role ##########
@router.get("/get/{role_id}")
async def get_roles(request: Request, role_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    permissions = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.roles.update")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    if not role_id:
        return custom_response(status_code=400, message=translate(lang, "platform.roles.get.single.error"))
    
    check_role = db.query(User_Role).filter(
        User_Role.id == role_id
    ).first()
    
    if not check_role:
        return custom_response(status_code=400, message=translate(lang, "platform.roles.get.single.error"))
        
    ### Operations ###
    permissions = get_permissions()

    permissions_selected = {
        "name": check_role.name,
        "description": check_role.description,
        "permissions": check_role.permissions,
        "hidden": check_role.hidden
    }
        
    return custom_response(status_code=200, message=translate(lang, "platform.roles.get.single.success"), data={
        "permissions": permissions,
        "permissions_selected": permissions_selected
    })

########## Post Role - To Update Role ##########
@router.post("/update/{role_id}")
async def get_roles(request: Request, role_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    permissions = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.roles.update")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    if not role_id:
        return custom_response(status_code=400, message=translate(lang, "platform.roles.get.single.error"))
    
    ### Get Body ###
    update_role, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(update_role, ["permissions", "role_name", "description", "hidden"])
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    check_role = db.query(User_Role).filter(
        User_Role.id == role_id
    ).first()

    if not check_role:
        return custom_response(status_code=400, message=translate(lang, "platform.roles.get.single.error"))
    
    permissions = filter_existing_permissions(update_role.permissions)
    print(permissions)

    check_role.name = update_role.role_name
    check_role.permissions = permissions
    check_role.description = update_role.description

    if update_role.hidden == "1":
        check_role.hidden = True
    else:
        check_role.hidden = False

    update_db(db)
        
    return custom_response(status_code=200, message=translate(lang, "platform.roles.update.single.success"), data={
        "role_id": check_role.id
    })
