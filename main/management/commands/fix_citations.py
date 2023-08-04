from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "This command will link all citations to their respective patents using" \
    "the citation.cited_patent_number and patent.patent_number. Useful utility for when" \
    "new patents are added to the database."

    def handle(self, *args, **options):
        pass
