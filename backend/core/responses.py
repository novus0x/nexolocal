########## Modules ##########
from typing import Optional, Any, List

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

########## Custom HTTP Response ##########
def custom_response(status_code: int = 200, message: str = "", details: Optional[List[str]] = None, data: Optional[Any] = None):
    return JSONResponse(
        status_code = status_code,
        content = {
            "status": status_code,
            "message": message,
            "details": details if details is not None else [],
            "data": jsonable_encoder(data) if data else {}
        }
    )
