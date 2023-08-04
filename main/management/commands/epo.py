from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "This command downloads and inserts to db all EPO granted patents through lens.org API."

    def handle(self, *args, **options):
        pass
