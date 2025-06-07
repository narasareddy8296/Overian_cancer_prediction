import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_TEMPLATES

def send_verification_email(to_email, name, verification_code):
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = EMAIL_TEMPLATES['verification']['subject']

        # Create body
        body = EMAIL_TEMPLATES['verification']['body'].format(
            name=name,
            code=verification_code
        )
        msg.attach(MIMEText(body, 'plain'))

        # Setup server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        # Send email
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, to_email, text)
        server.quit()
        return True

    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def generate_verification_code():
    """Generate a 6-digit verification code"""
    from random import randint
    return str(randint(100000, 999999))
