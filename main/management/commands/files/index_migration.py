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
        # RunSQL("CREATE INDEX main_cpcgroup_group_idx ON main_cpcgroup USING GIST (group gist_trgm_ops);", 
        #     reverse_sql="DROP INDEX main_cpcgroup_group_idx;"),
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
        # RunSQL("CREATE INDEX main_patent_title_idx ON main_patent USING GIN (title gin_trgm_ops);",
        #     reverse_sql="DROP INDEX main_patent_title_idx;"), # full text search doesn't work well with texts, and most of the design patents have single or few words titles
        # RunPython(lambda *_: print("Patent indexes created."), reverse_code=lambda *_: print("Patent indexes dropped.")),
        
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
        # RunSQL("CREATE INDEX main_inventor_first_name_idx ON main_inventor USING GIN (first_name gin_trgm_ops);",
        #     reverse_sql="DROP INDEX main_inventor_first_name_idx;"),
        # RunSQL("CREATE INDEX main_inventor_last_name_idx ON main_inventor USING GIN (last_name gin_trgm_ops);",
        #     reverse_sql="DROP INDEX main_inventor_last_name_idx;"),
        # RunPython(lambda *_: print("Inventor indexes created."), reverse_code=lambda *_: print("Inventor indexes dropped.")),

        # AddIndex("Assignee", Index(fields=["patent"], name="main_assignee_patent_idx")),
        # AddIndex("Assignee", Index(fields=["location"], name="main_assignee_location_idx")),
        # RunSQL("CREATE INDEX main_assignee_first_name_idx ON main_assignee USING GIN (first_name gin_trgm_ops);",
        #     reverse_sql="DROP INDEX main_assignee_first_name_idx;"),
        # RunSQL("CREATE INDEX main_assignee_last_name_idx ON main_assignee USING GIN (last_name gin_trgm_ops);",
        #     reverse_sql="DROP INDEX main_assignee_last_name_idx;"),
        # RunSQL("CREATE INDEX main_assignee_organization_idx ON main_assignee USING GIN (organization gin_trgm_ops);",
        #     reverse_sql="DROP INDEX main_assignee_organization_idx;"),
        # RunPython(lambda *_: print("Assignee indexes created."), reverse_code=lambda *_: print("Assignee indexes dropped.")),

        # AddIndex("PatentCitation", Index(fields=["citing_patent"], name="main_patentcitation_citing_patent_idx")),
        # AddIndex("PatentCitation", Index(fields=["cited_patent"], name="main_patentcitation_cited_patent_idx")),
        # RunPython(lambda *_: print("PatentCitation indexes created."), reverse_code=lambda *_: print("PatentCitation indexes dropped.")),
    ]   
