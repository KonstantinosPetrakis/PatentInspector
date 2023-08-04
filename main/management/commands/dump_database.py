from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "This command will dump the entire database into a file."

    def handle(self, *args, **options):
        pass
