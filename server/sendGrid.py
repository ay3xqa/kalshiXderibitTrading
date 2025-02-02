# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import os
from sendgrid import SendGridAPIClient
import certifi
from sendgrid.helpers.mail import Mail

def send_email(html_content):
    """
    Send an email using SendGrid with hardcoded sender, recipients, and subject
    
    Args:
        html_content (str): Email content in HTML format
        
    Returns:
        dict: Response containing status_code, body, and headers
    """
    from_email = "isaacjhuntsman@gmail.com"  # Replace with your sender email
    to_emails = ["u1180745@utah.edu", "alexlyu5.ay@gmail.com"]  # List of recipient emails
    subject = "Trade Alert"
    
    message = Mail(
        from_email=from_email,
        to_emails=to_emails,
        subject=subject,
        html_content=html_content)
    
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        sg.clients.ca_certs=certifi.where()
        response = sg.send(message)
        return {
            'status_code': response.status_code,
            'body': response.body,
            'headers': response.headers
        }
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")