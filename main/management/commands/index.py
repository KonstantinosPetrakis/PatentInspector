from django.core.management.base import BaseCommand
import os
from shutil import copy2 as copy


class Command(BaseCommand):
    help = "This command creates or drops the indexes in the database."

    def handle(self, *args, **options):
        command = input("What do you want to do? (create/drop): ")
        if command == "create":
            copy(
                "./main/management/commands/files/index_migration.py",
                "./main/migrations/",
            )
            os.system("python manage.py migrate main")
        elif command == "drop":
            os.system("python manage.py migrate main 0001_initial")
            os.remove("./main/migrations/index_migration.py")
        else:
            print("Invalid command.")
