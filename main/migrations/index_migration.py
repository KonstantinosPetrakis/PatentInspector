from django.contrib.postgres.search import SearchVector      
from django.db.migrations import Migration, AddIndex, RunPython, RunSQL
from django.contrib.postgres.indexes import GinIndex, GistIndex
from django.db.models.indexes import Index


def index_entries(apps, schema_editor):
    Patent = apps.get_model("main", "Patent")
    Patent.objects.update(search_vector=SearchVector("title", "abstract"))


class Migration(Migration):
    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        # Add trigger to update the search vector field.
        RunSQL(
            sql="""
            CREATE TRIGGER update_search_vector BEFORE INSERT OR UPDATE OF title, abstract
            ON main_patent
            FOR EACH ROW EXECUTE PROCEDURE
            tsvector_update_trigger(search_vector, 'pg_catalog.english', title, abstract);
            UPDATE main_patent SET search_vector = NULL;
            """,
            reverse_sql="""
            DROP TRIGGER IF EXISTS update_search_vector ON main_patent;
            """
        ),

        # Populate the search vector field.
        RunPython(index_entries),

        # Create the indexes.
        # ~ CPCGroup ~
        AddIndex("CPCGroup", Index(fields=["subclass"], name="main_cpcgroup_subclass_idx")),
        
        # ~ Patent ~
        AddIndex("Patent", Index(fields=["type"], name="main_patent_type_idx")),
        AddIndex("Patent", GinIndex(fields=["search_vector"], name="main_patent_search_vector_idx")),
        
        # ~ PatentCPCGroup ~
        AddIndex("PatentCPCGroup", Index(fields=["patent"], name="main_patentcpcgroup_patent_idx")),
        AddIndex("PatentCPCGroup", Index(fields=["cpc_group"], name="main_patentcpcgroup_cpc_group_idx")),
        
        # ~ PCTData ~
        AddIndex("PCTData", Index(fields=["patent"], name="main_pctdata_patent_idx")),
        AddIndex("PCTData", Index(fields=["published_or_filed_date"], name="main_pctdata_published_or_filed_date_idx")),

        # ~ Location ~
        AddIndex("location", GistIndex(fields=["point"], name="main_location_point_idx")),

        # ~ Inventor ~
        AddIndex("Inventor", Index(fields=["patent"], name="main_inventor_patent_idx")),
        AddIndex("Inventor", Index(fields=["location"], name="main_inventor_location_idx")),
        AddIndex("Inventor", Index(fields=["first_name"], name="main_inventor_first_name_idx")),
        AddIndex("Inventor", Index(fields=["last_name"], name="main_inventor_last_name_idx")),

        # ~ Assignee ~
        AddIndex("Assignee", Index(fields=["patent"], name="main_assignee_patent_idx")),
        AddIndex("Assignee", Index(fields=["location"], name="main_assignee_location_idx")),
        AddIndex("Assignee", Index(fields=["first_name"], name="main_assignee_first_name_idx")),
        AddIndex("Assignee", Index(fields=["last_name"], name="main_assignee_last_name_idx")),
        AddIndex("Assignee", Index(fields=["organization"], name="main_assignee_organization_idx")),

        # ~ PatentCitation ~
        AddIndex("PatentCitation", Index(fields=["citing_patent"], name="main_patentcitation_citing_patent_idx")),
        AddIndex("PatentCitation", Index(fields=["cited_patent"], name="main_patentcitation_cited_patent_idx")),
    ]   
