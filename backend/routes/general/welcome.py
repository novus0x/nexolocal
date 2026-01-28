########## Modules ##########
from fastapi import APIRouter, Request, Depends

from core.responses import custom_response

########## Variables ##########
router = APIRouter()

########## Welcome - Test ##########
@router.get("/welcome")
async def welcome(request: Request):
    return custom_response(status_code=200, message="Welcome")

