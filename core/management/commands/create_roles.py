import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nde_digital.settings') # Replace with your project's settings
django.setup()

from core.models import Role  # Assuming your Role model is in the 'core' app
from django.core.management.base import BaseCommand  # Import BaseCommand

class Command(BaseCommand):  # Define the Command class
    help = 'Creates default roles for the application.'

    def handle(self, *args, **options):
        roles_data = [
            {'name': 'DG', 'description': 'Director General'},
            {'name': 'DIR', 'description': 'Director'},
            {'name': 'ZD', 'description': 'Zonal Director'},
            {'name': 'HOD', 'description': 'Head of Department'},
            {'name': 'SD', 'description': 'State Director'},
            {'name': 'LIASON', 'description': 'LGA Liaison Officer'},
        ]

        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'], 
                defaults={'description': role_data['description']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Role '{role.name}' created successfully."))
            else:
                self.stdout.write(self.style.WARNING(f"Role '{role.name}' already exists."))
