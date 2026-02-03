########## Modules ##########
import os

from types import SimpleNamespace
from jinja2 import Environment, FileSystemLoader, select_autoescape

########## Variables ##########
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

template_routes = SimpleNamespace(
    auth = SimpleNamespace(
        welcome = "auth/welcome.html",
        reset_password = "auth/reset-password.html"
    ),
    oauth = SimpleNamespace(
        google = "oauth/password-google.html"
    ),
    account = SimpleNamespace(
        password_updated = "account/password-updated.html"
    )
)

########## Settings ##########
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(["html", "xml"]), enable_async=True)

########## Render HTML ##########
async def get_html(template_name: str, context: dict):
    template = env.get_template(template_name)
    return await template.render_async(**context)
