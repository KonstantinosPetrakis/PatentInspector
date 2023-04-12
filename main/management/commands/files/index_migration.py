from django.db.migrations import Migration, AddIndex, RunPython, RunSQL
from django.contrib.postgres.indexes import GistIndex, GinIndex
from django.db.models.indexes import Index


class Migration(Migration):
    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        RunPython(lambda *_: print("\n"), reverse_code=lambda *_: print("\n")),

        # AddIndex("CPCGroup", Index(fields=["subclass"], name="main_cpcgroup_subclass_idx")),
        # RunPython(lambda *_: print("CPCGroup indexes created."), reverse_code=lambda *_: print("CPCGroup indexes dropped.")),

        # RunSQL("""
        #         ALTER TABLE main_patent DROP COLUMN IF EXISTS search; 
        #         ALTER TABLE main_patent ADD search TSVECTOR GENERATED ALWAYS AS (
        #             setweight(to_tsvector('english', title), 'A') || ' ' ||
        #             setweight(to_tsvector('english', abstract), 'B') :: TSVECTOR
        #         ) STORED;""",
        #     reverse_sql="ALTER TABLE main_patent DROP COLUMN search;"
        # ),
        # RunSQL("CREATE INDEX main_patent_search_idx ON main_patent USING GIN (search);",
        #     reverse_sql="DROP INDEX main_patent_search_idx;"),

        RunPython(lambda *_: print("Patent indexes created."), reverse_code=lambda *_: print("Patent indexes dropped.")),
        
        # AddIndex("PatentCPCGroup", Index(fields=["patent"], name="main_patentcpcgroup_patent_idx")),
        # AddIndex("PatentCPCGroup", Index(fields=["cpc_group"], name="main_patentcpcgroup_cpc_group_idx")),
        # RunPython(lambda *_: print("PatentCPCGroup indexes created."), reverse_code=lambda *_: print("PatentCPCGroup indexes dropped.")),
        
        # AddIndex("PCTData", Index(fields=["patent"], name="main_pctdata_patent_idx")),
        # AddIndex("PCTData", Index(fields=["published_or_filed_date"], name="main_pctdata_published_or_filed_date_idx")),
        # RunPython(lambda *_: print("PCTData indexes created."), reverse_code=lambda *_: print("PCTData indexes dropped.")),

        # AddIndex("location", GistIndex(fields=["point"], name="main_location_point_idx")),
        # RunPython(lambda *_: print("Location indexes created."), reverse_code=lambda *_: print("Location indexes dropped.")),

        # AddIndex("Inventor", Index(fields=["patent"], name="main_inventor_patent_idx")),
        # AddIndex("Inventor", Index(fields=["location"], name="main_inventor_location_idx")),
        # AddIndex("Inventor", Index(fields=["first_name"], name="main_inventor_first_name_idx")),
        # AddIndex("Inventor", Index(fields=["last_name"], name="main_inventor_last_name_idx")),
        # RunPython(lambda *_: print("Inventor indexes created."), reverse_code=lambda *_: print("Inventor indexes dropped.")),

        # AddIndex("Assignee", Index(fields=["patent"], name="main_assignee_patent_idx")),
        # AddIndex("Assignee", Index(fields=["location"], name="main_assignee_location_idx")),
        # AddIndex("Assignee", Index(fields=["first_name"], name="main_assignee_first_name_idx")),
        # AddIndex("Assignee", Index(fields=["last_name"], name="main_assignee_last_name_idx")),
        # AddIndex("Assignee", Index(fields=["organization"], name="main_assignee_organization_idx")),
        # RunPython(lambda *_: print("Assignee indexes created."), reverse_code=lambda *_: print("Assignee indexes dropped.")),

        # AddIndex("PatentCitation", Index(fields=["citing_patent"], name="main_patentcitation_citing_patent_idx")),
        # AddIndex("PatentCitation", Index(fields=["cited_patent"], name="main_patentcitation_cited_patent_idx")),
        # RunPython(lambda *_: print("PatentCitation indexes created."), reverse_code=lambda *_: print("PatentCitation indexes dropped.")),
    ]   
