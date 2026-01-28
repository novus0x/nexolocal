from fastapi import Request

def detect_accept_language(header_value: str):
    print(header_value)
    try:
        return header_value.split(",")[0].split("-")[0]
    except:
        return "en"

async def i18n_middleware(request: Request, call_next):
    lang = "en"

    user = getattr(request.state, "user", None)
    if user and "preferred_language" in user:
        lang = user["preferred_language"]
    elif "accept-language" in request.headers:
        lang = detect_accept_language(request.headers["accept-language"])
    
    request.state.lang = lang
    # print("Lang: ", request.state.lang)

    return await call_next(request)
