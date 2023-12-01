from django.db.migrations import Migration, AddIndex, RunPython, RunSQL


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
            'CREATE INDEX main_ipcsubroup_subgroup_idx ON main_ipcsubgroup USING GIN ("subgroup" gin_trgm_ops);',
            reverse_sql="DROP INDEX main_ipcsubroup_subgroup_idx;",
        ),
        RunSQL(
            'CREATE INDEX main_ipcgroup_group_idx ON main_ipcgroup USING GIN ("group" gin_trgm_ops);',
            reverse_sql="DROP INDEX main_ipcgroup_group_idx;",
        ),
        RunPython(
            lambda *_: print("IPCGroup indexes created."),
            reverse_code=lambda *_: print("IPCGroup indexes dropped."),
        ),
        RunSQL(
            "CREATE INDEX main_patent_title_abstract_idx ON main_patent USING GIN (title_processed gin_trgm_ops, abstract_processed gin_trgm_ops);",
            reverse_sql="DROP INDEX main_patent_title_abstract_idx;",
        ),
        RunSQL(
            "CREATE INDEX main_patent_granted_year_idx ON main_patent (granted_year);",
            reverse_sql="DROP INDEX main_patent_granted_year_idx;",
        ),
        RunSQL(
            "CREATE INDEX main_patent_application_year_idx ON main_patent (application_year);",
            reverse_sql="DROP INDEX main_patent_application_year_idx;",
        ),
        RunSQL(
            "CREATE INDEX main_patent_granted_date_idx ON main_patent (granted_date);",
            reverse_sql="DROP INDEX main_patent_granted_date_idx;",
        ),
        RunSQL(
            "CREATE INDEX main_patent_application_filed_date_idx ON main_patent (application_filed_date);",
            reverse_sql="DROP INDEX main_patent_application_filed_date_idx;",
        ),
        RunPython(
            lambda *_: print("Patent indexes created."),
            reverse_code=lambda *_: print("Patent indexes dropped."),
        ),
        RunSQL(
            "CREATE INDEX main_pctdata_published_or_filed_date_idx ON main_pctdata (published_or_filed_date);",
            reverse_sql="DROP INDEX main_pctdata_published_or_filed_date_idx;",
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
            "CREATE INDEX main_assignee_organization_idx ON main_assignee USING GIN (organization gin_trgm_ops);",
            reverse_sql="DROP INDEX main_assignee_organization_idx;",
        ),
        RunPython(
            lambda *_: print("Assignee indexes created."),
            reverse_code=lambda *_: print("Assignee indexes dropped."),
        ),
        RunSQL(
            "CREATE INDEX main_patentcitation_citation_year_idx ON main_patentcitation (citation_year);",
            reverse_sql="DROP INDEX main_patentcitation_citation_year_idx;",
        ),
        RunPython(
            lambda *_: print("PatentCitation indexes created."),
            reverse_code=lambda *_: print("PatentCitation indexes dropped."),
        ),
    ]
