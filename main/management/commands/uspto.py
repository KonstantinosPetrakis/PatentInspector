from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'This command downloads all the necessary data from the USPTO'

    def handle(self, *args, **options):
        print("Hello World")

        # Interesting tables:
        # https://patentsview.org/download/data-download-tables
        # https://patentsview.org/download/data-download-dictionary
        # https://s3.amazonaws.com/community.patentsview.org/PatentsView+Data+Logic+Diagram+FINAL.jpg