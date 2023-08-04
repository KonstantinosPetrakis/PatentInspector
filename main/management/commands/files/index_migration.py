from django.db.migrations import Migration, AddIndex, RunPython, RunSQL
from django.db.models.indexes import Index


class Migration(Migration):
    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        RunPython(lambda *_: print("\n"), reverse_code=lambda *_: print("\n")),
        RunSQL(
            'CREATE INDEX main_cpcgroup_group_idx ON main_cpcgroup USING GIN ("group" gin_trgm_ops);',
            reverse_sql="DROP INDEX main_cpcgroup_group_idx;",
        ),
        RunPython(
            lambda *_: print("CPCGroup indexes created."),
            reverse_code=lambda *_: print("CPCGroup indexes dropped."),
        ),
        RunSQL(
            "CREATE INDEX main_patent_title_abstract_idx ON main_patent USING GIN (title gin_trgm_ops, abstract gin_trgm_ops);",
            reverse_sql="DROP INDEX main_patent_title_abstract_idx;",
        ),
        AddIndex(
            "Patent",
            Index(fields=["granted_year"], name="main_patent_granted_year_idx"),
        ),
        AddIndex(
            "Patent",
            Index(fields=["application_year"], name="main_patent_application_year_idx"),
        ),
        AddIndex(
            "Patent",
            Index(fields=["granted_date"], name="main_patent_granted_date_idx"),
        ),
        AddIndex(
            "Patent",
            Index(
                fields=["application_filed_date"],
                name="main_patent_application_filed_date_idx",
            ),
        ),
        RunPython(
            lambda *_: print("Patent indexes created."),
            reverse_code=lambda *_: print("Patent indexes dropped."),
        ),
        AddIndex(
            "PCTData",
            Index(
                fields=["published_or_filed_date"],
                name="main_pctdata_published_or_filed_date_idx",
            ),
        ),
        RunPython(
            lambda *_: print("PCTData indexes created."),
            reverse_code=lambda *_: print("PCTData indexes dropped."),
        ),
        RunSQL(
            "CREATE INDEX main_inventor_first_name_idx ON main_inventor USING GIN (first_name gin_trgm_ops);",
            reverse_sql="DROP INDEX main_inventor_first_name_idx;",
        ),
        RunSQL(
            "CREATE INDEX main_inventor_last_name_idx ON main_inventor USING GIN (last_name gin_trgm_ops);",
            reverse_sql="DROP INDEX main_inventor_last_name_idx;",
        ),
        RunPython(
            lambda *_: print("Inventor indexes created."),
            reverse_code=lambda *_: print("Inventor indexes dropped."),
        ),
        RunSQL(
            "CREATE INDEX main_assignee_first_name_idx ON main_assignee USING GIN (first_name gin_trgm_ops);",
            reverse_sql="DROP INDEX main_assignee_first_name_idx;",
        ),
        RunSQL(
            "CREATE INDEX main_assignee_last_name_idx ON main_assignee USING GIN (last_name gin_trgm_ops);",
            reverse_sql="DROP INDEX main_assignee_last_name_idx;",
        ),
        RunSQL(
            "CREATE INDEX f ON main_assignee_organization_idx USING GIN (organization gin_trgm_ops);",
            reverse_sql="DROP INDEX main_assignee_organization_idx;",
        ),
        RunPython(
            lambda *_: print("Assignee indexes created."),
            reverse_code=lambda *_: print("Assignee indexes dropped."),
        ),
        AddIndex(
            "PatentCitation",
            Index(
                fields=["citation_year"], name="main_patentcitation_citation_year_idx"
            ),
        ),
        RunPython(
            lambda *_: print("PatentCitation indexes created."),
            reverse_code=lambda *_: print("PatentCitation indexes dropped."),
        ),
    ]
