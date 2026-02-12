########## Modules ##########
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request, Depends

from sqlalchemy import desc, asc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User, Ticket_Priority, Ticket_Category, Ticket, Ticket_Response, Ticket_Waiting_For

from core.config import settings

from core.i18n import translate
from core.responses import custom_response
from core.permissions import check_permissions
from core.db_management import add_db, update_db
from core.generator import get_uuid, generate_nxid
from core.validators import read_json_body, validate_required_fields

########## Variables ##########
router = APIRouter()
TIMEZONE = settings.TIMEZONE

LOCAL_TZ = ZoneInfo(TIMEZONE)
UTZ_TZ = ZoneInfo("UTC")

########## Create new Ticket Support - API ##########
@router.post("/tickets/create")
async def create_new_ticket_support(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Get Body ###
    check_ticket, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(check_ticket, [
        "category", "priority", "title", "description"
    ])

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    if not check_ticket.category in Ticket_Category._value2member_map_:
        return custom_response(status_code=400, message=translate(lang, "general.support.ticket.create.error.incorrect_option"), details=required_fields)

    if not check_ticket.priority in Ticket_Priority._value2member_map_:
        return custom_response(status_code=400, message=translate(lang, "general.support.ticket.create.error.incorrect_option"), details=required_fields)

    code_generated = generate_nxid("ticket")

    while 1:
        if db.query(Ticket).filter(Ticket.code == code_generated).first():
            code_generated = generate_nxid("ticket")
        else:
            break

    new_ticket = Ticket(
        id = get_uuid(db, Ticket),
        code = code_generated,

        title = check_ticket.title,

        priority = Ticket_Priority(check_ticket.priority),
        category = Ticket_Category(check_ticket.category),

        created_by_id = user.get("id")
    )
    
    new_ticket_item = Ticket_Response(
        id = get_uuid(db, Ticket_Response),

        content_html = check_ticket.description,

        user_id = user.get("id"),
        ticket_id = new_ticket.id
    )

    add_db(db, new_ticket)
    add_db(db, new_ticket_item)

    return custom_response(status_code=200, message=translate(lang, "general.support.ticket.create.success"), data={
        "ticket_code": new_ticket.code
    })

########## Get Tickets - API ##########
@router.get("/tickets")
async def get_tickets(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    tickets = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    tickets_data = db.query(Ticket).filter(
        Ticket.created_by_id == user.get("id")
    ).order_by(desc(Ticket.date)).all()

    for ticket in tickets_data:
        tickets.append({
            "id": ticket.id,
            "code": ticket.code,
            "title": ticket.title,
            "waiting_for": ticket.waiting_for,
            "date": ticket.date.astimezone(LOCAL_TZ).strftime("%H:%M - %d %b %Y")
        })

    return custom_response(status_code=200, message=translate(lang, "platform.support.tickets.get"), data={
        "tickets": tickets
    })

########## Get Tickets - API ##########
@router.get("/tickets/get/{ticket_id}")
async def get_ticket_by_id(request: Request, ticket_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ticket = {}
    ticket_items = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Main Ticket ###
    ticket_data = db.query(Ticket).filter(
        Ticket.code == ticket_id
    ).first()

    if not ticket_data:
        return custom_response(status_code=400, message=translate(lang, "general.support.tickets.get.unique.error"))
    
    ### Check for User ###
    user_data = db.query(User).filter(
        User.id == ticket_data.created_by_id
    ).first()

    if not user_data:
        return custom_response(status_code=400, message=translate(lang, "general.support.tickets.get.unique.error"))  
    elif ticket_data.created_by_id != user_data.id: # Validation
        return custom_response(status_code=400, message=translate(lang, "general.support.tickets.get.unique.error"))  

    ticket_items_data = db.query(Ticket_Response).filter(
        Ticket_Response.ticket_id == ticket_data.id,
        Ticket_Response.is_public == True
    ).order_by(asc(Ticket_Response.date)).all()

    for ticket_item in ticket_items_data:
        user_ticket_item = {}

        user_ticket_item_data = db.query(User).filter(
            User.id == ticket_item.user_id
        ).first()

        if user_ticket_item_data:
            user_ticket_item = {
                "id": user_ticket_item_data.id,
                "fullname": user_ticket_item_data.fullname,
                "staff": ticket_item.staff_response
            }

        ticket_item_date = ticket_item.date.astimezone(LOCAL_TZ).strftime("%H:%M - %d %b %Y")
        
        ticket_items.append({
            "id": ticket_item.id,
            "content": ticket_item.content_html,
            "is_final": ticket_item.is_final,
            "date": ticket_item_date,
            "user": user_ticket_item
        })

    ticket = {
        "id": ticket_data.id,
        "code": ticket_data.code,

        "title": ticket_data.title,
        "description": ticket_data.description,

        "priority": ticket_data.priority,
        "category": ticket_data.category,
        "waiting_for": ticket_data.waiting_for,

        "date": ticket_data.date,

        "items": ticket_items
    }

    return custom_response(status_code=200, message=translate(lang, "general.support.ticket.response.create.success"), data={
        "ticket": ticket
    })

########## Create Response - API ##########
@router.post("/tickets/{ticket_id}/response/create")
async def create_new_ticket_response(request: Request, ticket_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check Ticket ###
    ticket_data = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket_data:
        return custom_response(status_code=400, message=translate(lang, "general.support.tickets.get.unique.error"))
    elif user.get("id") != ticket_data.created_by_id:
        return custom_response(status_code=400, message=translate(lang, "general.support.tickets.get.unique.error"))
    
    ### Get Body ###
    check_new_response, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)
        
    required_fields, error = validate_required_fields(check_new_response, ["description"])
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    new_response = Ticket_Response(
        id = get_uuid(db, Ticket_Response),
        content_html = check_new_response.description,
        staff_response = False,

        user_id = user.get("id"),
        ticket_id = ticket_data.id
    )

    ticket_data.waiting_for = Ticket_Waiting_For.SUPPORT

    add_db(db, new_response)
    update_db(db)

    return custom_response(status_code=200, message=translate(lang, "general.support.ticket.response.create.success"), data={})
