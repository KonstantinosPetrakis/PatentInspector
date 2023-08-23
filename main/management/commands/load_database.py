from django.core.management.base import BaseCommand
import environ

from main.management.backup_helper import backup


env = environ.Env()
environ.Env.read_env(".env")


class Command(BaseCommand):
    help = "This command will load the entire database from a dump file."

    def handle(self, *args, **options):
        backup(env("DOWNLOAD_BACKUP_URL"), env("POSTGRES_DB"))
