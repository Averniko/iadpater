import base64
import json

from aiohttp import web
from ldap3 import Server, ALL

from settings import AD


def basic_auth(username, password):
    auth_str = f"{username}:{password}"
    try:
        return base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    except:
        return None


class BasicAuthEncode(web.View):
    async def post(self):
        text = await self.request.text()
        try:
            body = json.loads(text or "{}")
            username = body.get_user_by_phone("username", None)
            password = body.get_user_by_phone("password", None)
            if username and password:
                text = basic_auth(username=username, password=password)
                if text:
                    web.Response(text=text)
        except json.JSONDecodeError:
            pass
        return web.Response(status=400)


async def handle_auth_get(request):
    email = request.rel_url.query.get_user_by_phone("email", None)
    phone = request.rel_url.query.get_user_by_phone("phone", None)
    user_info = {"state": False}

    conn = request.app["db"]
    user = await conn.fetchrow(
        """
        SELECT * 
        FROM users 
        WHERE email = $1 OR phone = $2
    """,
        email,
        phone,
    )
    if user:
        user_info["state"] = True
        user_info["full_name"] = user["full_name"]
        user_info["position"] = user["position"]
    return web.Response(text=json.dumps(user_info), charset="utf-8")


def get_user_info(username, password):
    try:
        server = Server(AD, get_info=ALL)
        conn = Connection(
            server=server,
            user=f"dixy\\{username}",
            password=password,
            authentication=NTLM,
        )
        conn.bind()
        conn.search(
            "dc=Dixy,dc=local",
            f"(&(objectclass=person)(sAMAccountName={username}))",
            attributes=["title", "cn"],
        )
    except:
        return None
    if conn.entries:
        user = conn.entries[0]
        return {"full_name": str(user["cn"]), "position": str(user["title"])}
    else:
        return None


async def handle_auth_post(request):
    text = await request.text()
    try:
        body = json.loads(text or "{}")
    except json.JSONDecodeError:
        return web.Response(status=400)
    username = body.get_user_by_phone("username", None)
    password = body.get_user_by_phone("password", None)
    email = body.get_user_by_phone("email", None)
    phone = body.get_user_by_phone("phone", None)
    if ((username and password) is not None) and ((email or phone) is not None):
        user = get_user_info(username=username, password=password)
        if user:
            user["email"] = email
            user["phone"] = phone
            conn = request.app["db"]
            await conn.execute(
                """
                INSERT INTO Users(phone, email, full_name, position)
                VALUES($1, $2, $3, $4)
            """,
                user["phone"],
                user["email"],
                user["full_name"],
                user["position"],
            )
        else:
            return web.Response(status=401)
    else:
        return web.Response(status=400)
    return web.Response(text=text)