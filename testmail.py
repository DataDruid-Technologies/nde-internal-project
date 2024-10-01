import os
from django.core.mail import send_mail
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nde_management_system.settings')
django.setup()

def send_test_email(subject, message, from_email, recipient_list):
    """Sends a test email to the specified recipient."""
    send_mail(subject, message, from_email, recipient_list)
    print("Test email sent successfully!")

if __name__ == '__main__':
    # Email details
    subject = 'Test Email from Django'
    message = 'This is a test email to check if your Django email configuration is working correctly.'
    from_email = 'info@nde-internal.org.ng'  # Configure this in settings.py
    recipient_list = ['billibukun@gmail.com']  # Recipient email address
    
    send_test_email(subject, message, from_email, recipient_list)
