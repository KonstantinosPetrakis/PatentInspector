"""
To use this command, you need to have a service account with Google Drive API enabled.
Additionally, you need to download the credentials json file and put in the root 
directory of the project with the name 'service-secrets.json'. 
More information here: 
"""

from os import system as _

from django.core.management.base import BaseCommand
import environ

from main.management.helpers import *


env = environ.Env()
environ.Env.read_env(".env")


class Command(BaseCommand):
    help = "This command will dump the entire database into a file."

    def handle(self, *args, **options):
        database = env("POSTGRES_DB")
        _(f"pg_dump -Fc {database} > dump")

        drive = GoogleDrive(login_with_service_account())
        if input("Do you want to delete old back ups: (y/n): ") == "y":
            for file in drive.ListFile({"q": f"title = 'patentinspector'"}).GetList():
                try:
                    file.Delete()
                except Exception:
                    pass  # It's ok if some files are not deleted.
            print("Old back ups deleted successfully.")

        new_folder = create_pubic_folder(drive)
        f = drive.CreateFile({"parents": [{"id": new_folder["id"]}], "title": "dump"})
        f.SetContentFile("dump")
        f.Upload()

        print("The file is available on:", f.metadata["webContentLink"])
