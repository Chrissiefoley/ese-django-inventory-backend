from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings
import logging


logger = logging.getLogger(__name__)


def send_low_stock_alert(item_name, current_stock, user_email):
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured - skipping email")
        return False

    try:
        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=user_email,
            subject=f'Low Stock Alert: {item_name}',
            html_content=f'''
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: #fff3cd;
                                border: 1px solid #ffc107; border-radius: 5px; padding: 20px;">
                        <h2 style="color: #856404;">Low Stock Alert</h2>
                        <p style="font-size: 16px;">The following item is running low on stock:</p>
                        <div style="background-color: white; padding: 15px;
                                    border-radius: 5px; margin: 15px 0;">
                            <p style="margin: 5px 0;"><strong>Item:</strong> {item_name}</p>
                            <p style="margin: 5px 0;"><strong>Current Stock:</strong>
                               <span style="color: #dc3545; font-weight: bold;">
                                   {current_stock} units</span></p>
                            <p style="margin: 5px 0;"><strong>Threshold:</strong>
                               {settings.LOW_STOCK_THRESHOLD} units</p>
                        </div>
                        <p style="font-size: 14px; color: #856404;">
                            <strong>Action Required:</strong> Please restock this item when next possible.
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="font-size: 12px; color: #6c757d;">
                            This is an automated alert from the SkySupperToSeat Inventory Management System.
                        </p>
                    </div>
                </body>
            </html>
            '''
        )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        logger.info(f"Low stock email sent for {item_name} to {user_email}: Status {response.status_code}")
        return True

    except Exception as e:
        logger.error(f"Failed to send low stock email: {str(e)}")
        return False
