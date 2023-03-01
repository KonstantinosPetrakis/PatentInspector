from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'This command downloads all the necessary data from the USPTO'

    def handle(self, *args, **options):
        print("Hello World")

        # Interesting tables (I might append some more):
        # g_application
        # g_claim
        # g_cpc_title
        # g_cpc_current
        # g_detail_desc_text
        # g_draw_desc_text
        # g_foreign_citation
        # g_inventor_disambiguated
        # g_patent (patent model)
        # g_pct_data
        # g_us_patent_citation
        # g_us_rel_doc
        # g_us_application_citation
        # g_assignee_disambiguated

        # https://patentsview.org/download/data-download-tables
        # https://patentsview.org/download/data-download-dictionary
        # https://s3.amazonaws.com/community.patentsview.org/PatentsView+Data+Logic+Diagram+FINAL.jpg