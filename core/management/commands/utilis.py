from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_styled_email(subject, template, context, recipient_list):
    """
    Send a styled email using an HTML template.
    
    :param subject: Email subject
    :param template: Path to the email template
    :param context: Dictionary containing context for the template
    :param recipient_list: List of recipient email addresses
    """
    # Add the logo URL to the context
    context['logo_url'] = f"{settings.BASE_DIR}/static/logos/nde_logo.png"
    
    # Render the HTML content
    html_content = render_to_string(template, context)
    
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