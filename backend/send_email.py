import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get('SENDGRID_API_KEY')
from_email = os.environ.get('FROM_EMAIL')
to_email = os.environ.get('TO_EMAIL')

def send_email():
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject='Sending with SendGrid is Fun',
        html_content='<strong>and easy to do anywhere, even with Python</strong>'
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)