from django.test import TestCase

# Create your tests here.
from django.core.mail import send_mail
from django.conf import settings

def test_email():
    subject = 'Test Email from NDE Internal Management System'
    message = 'This is a test email sent from the Django application.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = ['recipient@example.com']  # Replace with a test email address

    try:
        send_mail(subject, message, from_email, recipient_list)
        print("Test email sent successfully!")
    except Exception as e:
        print(f"Failed to send test email. Error: {str(e)}")

if __name__ == "__main__":
    test_email()