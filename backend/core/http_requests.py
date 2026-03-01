########## Modules ##########
import httpx

########## GET ##########
async def api_get(url: str, params: dict = None, headers: dict = None):
    async with httpx.AsyncClient() as client:
        res = await client.get(url, params=params, headers=headers)

        return res.json()

########## POST ##########
async def api_post(url: str, data: dict = None, headers: dict = None):
    async with httpx.AsyncClient() as client:
        res = await client.post(url, json=data, headers=headers)

        return res.json()

########## PUT ##########
async def api_put(url: str, data: dict = None, headers: dict = None):
    async with httpx.AsyncClient() as client:
        res = await client.put(url, json=data, headers=headers)

        return res.json()

########## DELETE ##########
async def api_delete(url: str, headers: dict = None):
    async with httpx.AsyncClient() as client:
        res = await client.delete(url, headers=headers)

        return res.json()
    
########## POST - FORM ##########
async def api_post_form(url: str, data: dict = None, headers: dict = None):
    async with httpx.AsyncClient() as client:
        res = await client.post(url, data=data, headers=headers)

        return res.json()
