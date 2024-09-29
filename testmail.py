# In your Django project, create a Python file (e.g., send_test_email.py)
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nde_management_system.settings')  # Replace 'your_project_name' with your actual project name

import django
django.setup()

from django.core.mail import send_mail

def send_test_email():
    subject = 'Test Email from Django'
    message = 'This is a test email to check if your Django email configuration is working correctly.'
    from_email = 'info@nde-internal.org.ng'  # Use the same email you configured in settings.py
    recipient_list = ['billibukun@gmail.com']  # The email address you want to send the test to

    send_mail(subject, message, from_email, recipient_list)
    print("Test email sent successfully!")

if __name__ == '__main__':
    send_test_email()