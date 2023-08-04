from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "This command will load the entire database from a dump file."

    def handle(self, *args, **options):
        pass
