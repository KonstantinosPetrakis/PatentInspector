from django.db import models
from django.utils.safestring import mark_safe
from django.core.cache import cache


def get_help_text(field):
    with open(f"main/help_texts/{field}.html", "r") as f:
        return mark_safe(f.read())


class Patent(models.Model):    
    @staticmethod
    def get_wipo_kind_choices():
        choices = cache.get("wipo_kind_choices")
        if choices is None:
            distinct_kinds = Patent.objects.values_list("wipo_kind", flat=True).distinct()
            choices = [(k, k) for k in distinct_kinds]
            cache.set("wipo_kind_choices", choices, timeout=3*60)
        return choices

    patent_type_choices = (
        ("utility", "Utility"),
        ("design", "Design"),
        ("plant", "Plant"),
        ("reissue", "Reissue")
    )

    office = models.CharField(max_length=100, help_text="The office that granted the patent.")
    office_patent_id = models.CharField(max_length=100, help_text="The ID of the patent in the office's database.")
    patent_type = models.CharField(max_length=100, choices=patent_type_choices, help_text=get_help_text("patent_type"))
    patent_date = models.DateField(help_text="The date when the patent was granted.")
    patent_title = models.TextField(help_text="The title of the patent.")
    patent_abstract = models.TextField(help_text="The abstract text of the patent.")
    wipo_kind = models.CharField(max_length=10, choices=get_wipo_kind_choices, help_text=get_help_text("wipo_kind"))
    num_claims = models.IntegerField(help_text="The number of claims in the patent.")
    withdrawn = models.BooleanField(help_text="Whether the patent has been withdrawn, in other words if it is still valid.")


class Application(models.Model):
    