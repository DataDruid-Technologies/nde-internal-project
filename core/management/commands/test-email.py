# core/management/commands/test-email.py

from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import os
from django.contrib.staticfiles.storage import staticfiles_storage

class Command(BaseCommand):
    help = 'Test email configuration with styled email'

    def handle(self, *args, **options):
        subject = 'Test Email from NDE Internal Management System'
        template_name = 'emails/email-templat.html'
        context = {
            'subject': subject,
            'message': "This is a test email from your Django application. If you're seeing this, your email configuration is working correctly!",
            'action_url': f"{settings.BASE_URL}/dashboard/",
            'action_text': 'Visit Dashboard',
            'logo_url': f"C:/Users/User/OneDrive/Desktop/Projects/External/nde-internal-project/static/logos/nde_logo..png",
        }
        recipient_list = ['billibukun@gmail.com']
        
        try:
            # Render the HTML content
            html_content = render_to_string(template_name, context)
            
            # Create a text-only version of the email
            text_content = strip_tags(html_content)
            
            # Create the email message
            email = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list
            )
            
            # Attach the HTML content
            email.attach_alternative(html_content, "text/html")
            
            # Send the email
            email.send()
            
            self.stdout.write(self.style.SUCCESS('Successfully sent styled test email'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send email: {str(e)}'))
            
        # Debug information
        self.stdout.write(f"Template path: {os.path.join(settings.BASE_DIR, 'templates', template_name)}")
        self.stdout.write(f"STATIC_URL: {settings.STATIC_URL}")
        self.stdout.write(f"STATIC_ROOT: {settings.STATIC_ROOT}")
        self.stdout.write(f"BASE_URL: {settings.BASE_URL}")
        self.stdout.write(f"Logo URL: {context['logo_url']}")