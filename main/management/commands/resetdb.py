from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from main.models import *
import environ
import shutil
import os


env = environ.Env()
environ.Env.read_env(".env")


class Command(BaseCommand):
    help = 'This command resets the database (deletes migrations, drops it, creates it, and create super user).'

    def handle(self, *args, **options):
        if input("Are you sure you want to reset the database? (y/n): ") != "y":
            return

        shutil.rmtree(f"{settings.BASE_DIR}/main/migrations", ignore_errors=True)
        os.makedirs(f"{settings.BASE_DIR}/main/migrations")
        os.system(f"dropdb {env('POSTGRES_DB')}")
        os.system(f"createdb {env('POSTGRES_DB')}")
        open(f"{settings.BASE_DIR}/main/migrations/__init__.py", "w").close()
        os.system("python manage.py makemigrations > /dev/null 2>&1")
        os.system("python manage.py migrate > /dev/null 2>&1")
        os.system("python manage.py loaddata cpc_section.json > /dev/null 2>&1")

        User.objects.create_superuser(
            username=env("ADMIN_USERNAME"),
            email=env("ADMIN_EMAIL"),
            password=env("ADMIN_PASSWORD"),
        ).save()

        print("Database reset successfully.")
