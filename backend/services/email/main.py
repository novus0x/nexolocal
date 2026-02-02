########## Modules ##########
import asyncio

from aiosmtplib import SMTP

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.config import settings

from services.email.credentials import EMAIL_FROM
from services.email.temps import template_routes, get_html

########## Variables ##########
shutdown_event = asyncio.Event()

########## Queue ##########
email_queue = asyncio.Queue()

########## Mail Worker ##########
async def send_mail_worker():
    while True:
        if shutdown_event.is_set() and email_queue.empty():
            break

        try:
            email_data = await asyncio.wait_for(
                email_queue.get(),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            continue

        smtp = None

        try:
            user_email = EMAIL_FROM[email_data["type"]]

            msg = MIMEMultipart("alternative")
            msg["Subject"] = email_data["subject"]
            msg["From"] = user_email
            msg["To"] = email_data["to_email"]
            msg.attach(MIMEText(email_data["html"], "html"))

            smtp = SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                start_tls=True
            )

            if settings.EMAIL_ENABLED:
                await smtp.connect()
                await smtp.login(settings.SMTP_USER, settings.SMTP_PASS)
                await smtp.send_message(msg)
            else:
                print("Email Mandado")

        except Exception as e:
            print("Email error:", e)

        finally:
            if smtp:
                await smtp.quit()

            email_queue.task_done()

    print("Mail worker drained queue and exited")

########## New email ##########
async def send_mail(type: str, subject: str, to_email: str, html: str):
    await email_queue.put({
        "type": type,
        "subject": subject,
        "to_email": to_email,
        "html": html
    })
