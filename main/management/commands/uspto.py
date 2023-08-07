"""
----------------------------------------------------------------------------------------------------
# What's this?
----------------------------------------------------------------------------------------------------
This module defines a command that downloads all the necessary data from the USPTO and inserts it to
the database.

----------------------------------------------------------------------------------------------------
# How does it work?
----------------------------------------------------------------------------------------------------
It uses pandas to preprocess the data.

For relatively small tables, it uses django's ORM bulk_create method to insert the data into the
database.

For larger tables, it uses the postgres_copy module to insert the data into the database for 
performance reasons.

----------------------------------------------------------------------------------------------------
# What are those fields and tables, how are they downloaded manually?
----------------------------------------------------------------------------------------------------
USPTO explains the tables and fields in the following URL:
https://patentsview.org/download/data-download-dictionary
Moreover, one can download the tables manually from the following URL:
https://patentsview.org/download/data-download-tables
"""

import zipfile
import os

from django.core.management.base import BaseCommand
from django.db.models import Subquery, OuterRef, Count, IntegerField
from django.contrib.gis.geos import Point
from django.conf import settings
import requests as r
import pandas as pd
import numpy as np

from main.models import *
from main.management.commands.helpers import *


# Constant definitions and initial setup
CHUNK_SIZE = 1000000  # Lower it if you have memory issues
DATA_DIRECTORY = f"{settings.BASE_DIR}/main/data"
ENDPOINT = "https://s3.amazonaws.com/data.patentsview.org/download/"
os.makedirs(DATA_DIRECTORY, exist_ok=True)

location_id_map = {}  # Will be used to map USPTO ids,
# to new generated IDs so relationships can be created.

patent_id_map = {}  # Will be used to map USPTO ids to new generated IDs
# so relationships can be created.


class Command(BaseCommand):
    help = 'This command downloads all the necessary data from the USPTO and inserts it  \
        "into the database.'

    def download_and_unzip(self, table: str):
        """
        Downloads and unzips a table from the USPTO endpoint.

        Args:
            table (str): The name of the table to download.
        """

        res = r.get(f"{ENDPOINT}{table}.tsv.zip")
        with open(f"{DATA_DIRECTORY}/{table}.tsv.zip", "wb") as f:
            f.write(res.content)

        with zipfile.ZipFile(f"{DATA_DIRECTORY}/{table}.tsv.zip", "r") as z:
            z.extractall(DATA_DIRECTORY)
        os.remove(f"{DATA_DIRECTORY}/{table}.tsv.zip")

    def handle_location(self):
        global location_id_map

        self.download_and_unzip("g_location_disambiguated")

        locations = pd.read_csv(
            f"{DATA_DIRECTORY}/g_location_disambiguated.tsv",
            sep="\t",
            usecols=[
                "location_id",
                "disambig_country",
                "disambig_state",
                "disambig_city",
                "longitude",
                "latitude",
                "county_fips",
                "state_fips",
            ],
            dtype={
                "location_id": str,
                "disambig_country": str,
                "disambig_state": str,
                "disambig_city": str,
                "longitude": float,
                "latitude": float,
                "county_fips": "Int64",
                "state_fips": "Int64",
            },
        )

        locations.rename(
            columns={
                "disambig_country": "country_code",
                "disambig_state": "state",
                "disambig_city": "city",
            },
            inplace=True,
        )

        location_old_ids = locations["location_id"].copy()
        locations.drop(columns=["location_id"], inplace=True)

        locations["point"] = locations.apply(
            lambda x: Point(x["longitude"], x["latitude"]), axis=1
        )
        locations.drop(columns=["longitude", "latitude"], inplace=True)
        locations = locations.astype(object).replace(np.nan, None).to_dict("records")

        locations = [Location(**location) for location in locations]
        Location.objects.bulk_create(locations)

        for i in range(len(location_old_ids)):
            location_id_map[location_old_ids[i]] = locations[i].id

        os.remove(f"{DATA_DIRECTORY}/g_location_disambiguated.tsv")
        print("Location table inserted successfully!")

    def handle_cpc(self):
        self.download_and_unzip("g_cpc_title")
        cpcs = pd.read_csv(f"{DATA_DIRECTORY}/g_cpc_title.tsv", sep="\t")

        # Create CPCClasses
        cpc_classes = cpcs.groupby("cpc_class", as_index=False)[
            ["cpc_class_title"]
        ].first()
        cpc_classes["section_id"] = cpc_classes["cpc_class"].str[0]
        cpc_classes = cpc_classes.rename(
            columns={"cpc_class": "_class", "cpc_class_title": "title"}
        )
        cpc_classes = [
            CPCClass(**cpc_class) for cpc_class in cpc_classes.to_dict("records")
        ]
        CPCClass.objects.bulk_create(cpc_classes)

        # Create CPCSubclasses
        cpc_subclasses = cpcs.groupby("cpc_subclass", as_index=False)[
            ["cpc_class", "cpc_subclass_title"]
        ].first()
        cpc_subclasses = cpc_subclasses.rename(
            columns={
                "cpc_class": "_class_id",
                "cpc_subclass": "subclass",
                "cpc_subclass_title": "title",
            }
        )
        cpc_subclasses = [
            CPCSubclass(**cpc_subclass)
            for cpc_subclass in cpc_subclasses.to_dict("records")
        ]
        CPCSubclass.objects.bulk_create(cpc_subclasses)

        # Create CPCGroups
        cpc_groups = cpcs[["cpc_group", "cpc_subclass", "cpc_group_title"]]
        cpc_groups = cpc_groups.rename(
            columns={
                "cpc_group": "group",
                "cpc_subclass": "subclass_id",
                "cpc_group_title": "title",
            }
        )
        cpc_groups = [
            CPCGroup(**cpc_group) for cpc_group in cpc_groups.to_dict("records")
        ]
        CPCGroup.objects.bulk_create(cpc_groups)

        os.remove(f"{DATA_DIRECTORY}/g_cpc_title.tsv")
        print("CPC tables inserted successfully!")

    def handle_patent(self):
        global patent_id_map

        self.download_and_unzip("g_patent")
        self.download_and_unzip("g_application")
        self.download_and_unzip("g_figures")

        # Preprocess data
        patents = pd.read_csv(
            f"{DATA_DIRECTORY}/g_patent.tsv",
            sep="\t",
            usecols=lambda col: col not in ["wipo_kind", "filename"],
            dtype={
                "patent_id": str,
                "patent_type": str,
                "patent_date": str,
                "patent_title": str,
                "patent_abstract": str,
                "num_claims": "Int64",
                "withdrawn": bool,
            },
            # Patents are big, so we will split them into small chunks
            chunksize=CHUNK_SIZE / 50, 
        )

        application = pd.read_csv(
            f"{DATA_DIRECTORY}/g_application.tsv",
            sep="\t",
            usecols=["patent_id", "filing_date"],
            dtype={"patent_id": str, "filing_date": str},
        )

        figures = pd.read_csv(
            f"{DATA_DIRECTORY}/g_figures.tsv",
            sep="\t",
            usecols=["patent_id", "num_figures", "num_sheets"],
            dtype={"patent_id": str, "num_figures": "Int64", "num_sheets": "Int64"},
        )

        for i, patent_chunk in enumerate(patents):
            patent_chunk = pd.merge(
                patent_chunk, application, on="patent_id", how="left"
            )

            patent_chunk = pd.merge(patent_chunk, figures, on="patent_id", how="left")

            patent_chunk = patent_chunk.astype(object).replace(np.nan, None)
            patent_chunk = patent_chunk.rename(
                columns={
                    "patent_id": "office_patent_id",
                    "patent_type": "type",
                    "patent_date": "granted_date",
                    "num_sheets": "sheets_count",
                    "filing_date": "application_filed_date",
                    "patent_title": "title",
                    "patent_abstract": "abstract_processed",
                    "num_figures": "figures_count",
                    "num_claims": "claims_count",
                }
            )

            # Drop invalid patents
            patent_chunk.drop(
                patent_chunk[
                    (patent_chunk["granted_date"].astype(bool) == False)
                    | (patent_chunk["application_filed_date"].astype(bool) == False)
                ].index,
                inplace=True,
            )

            patent_chunk.drop(
                patent_chunk[
                    ~(
                        patent_chunk["application_filed_date"].str.contains(
                            "^\d{4}-\d{2}-\d{2}$"
                        )
                    )
                    | ~(
                        patent_chunk["granted_date"].str.contains("^\d{4}-\d{2}-\d{2}$")
                    )
                ].index,
                inplace=True,
            )

            patent_chunk["office"] = "US"

            # Precalculate fields
            patent_chunk["granted_year"] = (
                patent_chunk["granted_date"].str[:4].astype("Int64")
            )
            patent_chunk["application_year"] = (
                patent_chunk["application_filed_date"].str[:4].astype("Int64")
            )
            patent_chunk["years_to_get_granted"] = (
                np.array(
                    multiprocessing_apply(
                        patent_chunk["granted_date"], string_to_timestamp
                    )
                )
                - np.array(
                    multiprocessing_apply(
                        patent_chunk["application_filed_date"], string_to_timestamp
                    )
                )
            ) / 31536000.0  # 365 * 24 * 60 * 60 seconds in a year
            patent_chunk["title_word_count_without_processing"] = (
                patent_chunk["title"].str.split().str.len()
            ).astype("Int64")
            patent_chunk["abstract_word_count_without_processing"] = (
                patent_chunk["abstract_processed"].str.split().str.len()
            ).astype("Int64")
            patent_chunk[
                ["title_word_count_with_processing", "title_processed"]
            ] = multiprocessing_apply(patent_chunk["title"], lemma_text)
            patent_chunk[
                ["abstract_word_count_with_processing", "abstract_processed"]
            ] = multiprocessing_apply(patent_chunk["abstract_processed"], lemma_text)

            patent_chunk.to_csv(
                f"{DATA_DIRECTORY}/g_patent_preprocessed.csv",
                index=False,
                header=i == 0,
                mode="a",
            )

        # Load data
        Patent.objects.from_csv(f"{DATA_DIRECTORY}/g_patent_preprocessed.csv")
        patent_id_map = {
            patent["office_patent_id"]: patent["id"]
            for patent in Patent.objects.filter(office="US").values(
                "id", "office_patent_id"
            )
        }

        os.remove(f"{DATA_DIRECTORY}/g_patent_preprocessed.csv")
        os.remove(f"{DATA_DIRECTORY}/g_patent.tsv")
        os.remove(f"{DATA_DIRECTORY}/g_application.tsv")
        os.remove(f"{DATA_DIRECTORY}/g_figures.tsv")
        print("Patent table inserted successfully!")

    def handle_patent_cpc_group(self):
        self.download_and_unzip("g_cpc_current")

        # Preprocess data
        valid_cpcs = CPCGroup.objects.values_list("group", flat=True)

        patent_cpc_groups = pd.read_csv(
            f"{DATA_DIRECTORY}/g_cpc_current.tsv",
            sep="\t",
            usecols=["patent_id", "cpc_group"],
            dtype={"patent_id": "str", "cpc_group": str},
            chunksize=CHUNK_SIZE,
        )

        for i, patent_cpc_groups_chunk in enumerate(patent_cpc_groups):
            patent_cpc_groups_chunk = patent_cpc_groups_chunk.rename(
                columns={"cpc_group": "cpc_group_id"}
            )
            patent_cpc_groups_chunk["patent_id"] = (
                patent_cpc_groups_chunk["patent_id"].map(patent_id_map).astype("Int64")
            )

            # Some CPC groups might have invalid patent ids, so we need to remove them
            patent_cpc_groups_chunk = patent_cpc_groups_chunk[
                patent_cpc_groups_chunk["patent_id"].notna()
            ]

            # About 800 patents have invalid CPC groups, so we need to ignore them
            patent_cpc_groups_chunk = patent_cpc_groups_chunk[
                patent_cpc_groups_chunk["cpc_group_id"].isin(valid_cpcs)
            ]

            patent_cpc_groups_chunk.to_csv(
                f"{DATA_DIRECTORY}/g_cpc_current_preprocessed.csv",
                index=False,
                header=i == 0,
                mode="a",
            )

        # Load data
        PatentCPCGroup.objects.from_csv(
            f"{DATA_DIRECTORY}/g_cpc_current_preprocessed.csv"
        )

        os.remove(f"{DATA_DIRECTORY}/g_cpc_current_preprocessed.csv")
        os.remove(f"{DATA_DIRECTORY}/g_cpc_current.tsv")
        print("PatentCPCGroup table inserted successfully!")

    def handle_pct(self):
        self.download_and_unzip("g_pct_data")

        # Preprocess data
        pct_data = pd.read_csv(
            f"{DATA_DIRECTORY}/g_pct_data.tsv",
            sep="\t",
            usecols=[
                "patent_id",
                "published_or_filed_date",
                "filed_country",
                "pct_doc_number",
                "pct_doc_type",
            ],
            dtype={
                "patent_id": str,
                "published_or_filed_date": str,
                "filed_country": str,
                "pct_doc_number": str,
                "pct_doc_type": str,
            },
            chunksize=CHUNK_SIZE,
        )

        for i, pct_data_chunk in enumerate(pct_data):
            pct_data_chunk.rename(
                columns={"pct_doc_number": "pct_id", "pct_doc_type": "granted"},
                inplace=True,
            )

            pct_data_chunk["patent_id"] = (
                pct_data_chunk["patent_id"].map(patent_id_map).astype("Int64")
            )
            pct_data_chunk["granted"] = pct_data_chunk["granted"].map(
                {"wo_grant": True, "pct_application": False}
            )

            # Remove rows that don't have a published or filed date or have an invalid patent id
            pct_data_chunk.drop(
                pct_data_chunk[
                    pct_data_chunk["patent_id"].isna()
                    | pct_data_chunk["published_or_filed_date"].isna()
                ].index,
                inplace=True,
            )

            # Precalculate fields
            pct_data_chunk["representation"] = pct_data_chunk[
                "published_or_filed_date"
            ] + pct_data_chunk["granted"].apply(
                lambda x: " - granted" if x else " - not granted"
            )

            pct_data_chunk.to_csv(
                f"{DATA_DIRECTORY}/g_pct_data_preprocessed.csv",
                index=False,
                header=i == 0,
                mode="a",
            )

        # Load data
        PCTData.objects.from_csv(f"{DATA_DIRECTORY}/g_pct_data_preprocessed.csv")

        os.remove(f"{DATA_DIRECTORY}/g_pct_data.tsv")
        os.remove(f"{DATA_DIRECTORY}/g_pct_data_preprocessed.csv")
        print("PCTData table inserted successfully!")

    def handle_inventor(self):
        self.download_and_unzip("g_inventor_disambiguated")

        # Preprocess data
        inventors_chunks = pd.read_csv(
            f"{DATA_DIRECTORY}/g_inventor_disambiguated.tsv",
            sep="\t",
            usecols=[
                "patent_id",
                "location_id",
                "disambig_inventor_name_first",
                "disambig_inventor_name_last",
                "gender_code",
            ],
            dtype={
                "patent_id": str,
                "location_id": str,
                "disambig_inventor_name_first": str,
                "disambig_inventor_name_last": str,
                "gender_code": object,
            },
            chunksize=CHUNK_SIZE,
        )

        for i, inventors_chunk in enumerate(inventors_chunks):
            # Process chunk
            inventors_chunk = inventors_chunk.rename(
                columns={
                    "disambig_inventor_name_first": "first_name",
                    "disambig_inventor_name_last": "last_name",
                    "gender_code": "male",
                }
            )

            inventors_chunk["patent_id"] = (
                inventors_chunk["patent_id"].map(patent_id_map).astype("Int64")
            )
            inventors_chunk["location_id"] = (
                inventors_chunk["location_id"].map(location_id_map).astype("Int64")
            )
            inventors_chunk = inventors_chunk[inventors_chunk["patent_id"].notna()]
            # There are some invalid location ids, so we need to remove them
            inventors_chunk = inventors_chunk[inventors_chunk["location_id"].notna()]
            inventors_chunk["location_id"] = inventors_chunk["location_id"].astype(
                "Int64"
            )
            inventors_chunk["male"] = inventors_chunk["male"].map(
                {"F": False, "M": True}
            )

            inventors_chunk.to_csv(
                f"{DATA_DIRECTORY}/g_inventor_disambiguated_preprocessed.csv",
                index=False,
                header=i == 0,
                mode="a",
            )

        # Load data
        Inventor.objects.from_csv(
            f"{DATA_DIRECTORY}/g_inventor_disambiguated_preprocessed.csv"
        )
        os.remove(f"{DATA_DIRECTORY}/g_inventor_disambiguated.tsv")
        os.remove(f"{DATA_DIRECTORY}/g_inventor_disambiguated_preprocessed.csv")
        print("Inventor table inserted successfully!")

    def handle_assignee(self):
        self.download_and_unzip("g_assignee_disambiguated")

        # Preprocess data
        assignee_chunks = pd.read_csv(
            f"{DATA_DIRECTORY}/g_assignee_disambiguated.tsv",
            sep="\t",
            usecols=[
                "patent_id",
                "location_id",
                "disambig_assignee_individual_name_first",
                "disambig_assignee_individual_name_last",
                "disambig_assignee_organization",
            ],
            dtype={
                "patent_id": str,
                "location_id": str,
                "disambig_assignee_organization": str,
                "disambig_assignee_individual_name_first": str,
                "disambig_assignee_individual_name_last": str,
            },
            chunksize=CHUNK_SIZE,
        )

        for i, assignee_chunk in enumerate(assignee_chunks):
            # Process chunk
            assignee_chunk = assignee_chunk.rename(
                columns={
                    "disambig_assignee_individual_name_first": "first_name",
                    "disambig_assignee_individual_name_last": "last_name",
                    "disambig_assignee_organization": "organization",
                }
            )

            assignee_chunk["patent_id"] = (
                assignee_chunk["patent_id"].map(patent_id_map).astype("Int64")
            )
            assignee_chunk["location_id"] = (
                assignee_chunk["location_id"].map(location_id_map).astype("Int64")
            )
            # There are some invalid location ids, so we need to remove them
            assignee_chunk = assignee_chunk[assignee_chunk["location_id"].notna()]
            assignee_chunk = assignee_chunk[assignee_chunk["patent_id"].notna()]

            # Precalculate fields
            assignee_chunk["is_organization"] = assignee_chunk["organization"].apply(
                lambda x: not pd.isnull(x)
            )

            assignee_chunk.to_csv(
                f"{DATA_DIRECTORY}/g_assignee_disambiguated_preprocessed.csv",
                index=False,
                header=i == 0,
                mode="a",
            )

        # Load data
        Assignee.objects.from_csv(
            f"{DATA_DIRECTORY}/g_assignee_disambiguated_preprocessed.csv"
        )

        os.remove(f"{DATA_DIRECTORY}/g_assignee_disambiguated_preprocessed.csv")
        os.remove(f"{DATA_DIRECTORY}/g_assignee_disambiguated.tsv")
        print("Assignee table inserted successfully!")

    def handle_us_patent_citation(self):
        global citations_made, citations_received
        self.download_and_unzip("g_us_patent_citation")

        # Preprocess data
        citations_chunks = pd.read_csv(
            f"{DATA_DIRECTORY}/g_us_patent_citation.tsv",
            sep="\t",
            usecols=["patent_id", "citation_patent_id", "citation_date"],
            dtype={"patent_id": str, "citation_patent_id": str, "citation_date": str},
            chunksize=CHUNK_SIZE,
        )

        for i, citations_chunk in enumerate(citations_chunks):
            citations_chunk.rename(
                columns={"patent_id": "citing_patent_id"}, inplace=True
            )

            citations_chunk["citing_patent_id"] = (
                citations_chunk["citing_patent_id"].map(patent_id_map).astype("Int64")
            )

            citations_chunk["cited_patent_id"] = (
                citations_chunk["citation_patent_id"].map(patent_id_map).astype("Int64")
            )

            # There could be cited patents that are not in the database, so we need to add their
            # number and country instead of their id
            na = citations_chunk["cited_patent_id"].isna()
            citations_chunk.loc[na, "cited_patent_office"] = "US"
            citations_chunk.loc[na, "cited_patent_number"] = citations_chunk.loc[
                na, "citation_patent_id"
            ]
            citations_chunk.drop(columns=["citation_patent_id"], inplace=True)

            # Precalculate fields
            citations_chunk["citation_year"] = (
                citations_chunk["citation_date"].str[:4].astype("Int64")
            )

            citations_chunk.to_csv(
                f"{DATA_DIRECTORY}/g_us_patent_citation_preprocessed.csv",
                index=False,
                header=i == 0,
                mode="a",
            )

        # Load data
        PatentCitation.objects.from_csv(
            f"{DATA_DIRECTORY}/g_us_patent_citation_preprocessed.csv"
        )

        os.remove(f"{DATA_DIRECTORY}/g_us_patent_citation.tsv")
        os.remove(f"{DATA_DIRECTORY}/g_us_patent_citation_preprocessed.csv")
        print("PatentCitation table (US) inserted successfully!")

    def handle_foreign_citation(self):
        global citations_made
        self.download_and_unzip("g_foreign_citation")

        # Preprocess data
        citations = pd.read_csv(
            f"{DATA_DIRECTORY}/g_foreign_citation.tsv",
            sep="\t",
            usecols=[
                "patent_id",
                "citation_application_id",
                "citation_date",
                "citation_country",
            ],
            dtype={
                "patent_id": str,
                "citation_application_id": str,
                "citation_date": str,
                "citation_country": str,
            },
            chunksize=CHUNK_SIZE,
        )

        for i, citation_chunk in enumerate(citations):
            citation_chunk.rename(
                columns={
                    "patent_id": "citing_patent_id",
                    "citation_application_id": "cited_patent_number",
                    "citation_country": "cited_patent_office",
                },
                inplace=True,
            )

            citation_chunk["citing_patent_id"] = (
                citation_chunk["citing_patent_id"].map(patent_id_map).astype("Int64")
            )

            # Precalculate fields
            citation_chunk["citation_year"] = (
                citation_chunk["citation_date"].str[:4].astype("Int64")
            )

            citation_chunk.to_csv(
                f"{DATA_DIRECTORY}/g_foreign_citation_preprocessed.csv",
                index=False,
                header=i == 0,
                mode="a",
            )

        # Load data
        PatentCitation.objects.from_csv(
            f"{DATA_DIRECTORY}/g_foreign_citation_preprocessed.csv"
        )

        os.remove(f"{DATA_DIRECTORY}/g_foreign_citation.tsv")
        os.remove(f"{DATA_DIRECTORY}/g_foreign_citation_preprocessed.csv")
        print("PatentCitation table (global) inserted successfully!")

    def handle_counts(self):
        Patent.objects.update(
            cpc_groups_count=Subquery(
                PatentCPCGroup.objects.filter(patent_id=OuterRef("id"))
                .values("patent_id")
                .annotate(count=Count("patent_id"))
                .values("count"),
                output_field=IntegerField(),
            ),
            assignee_count=Subquery(
                Assignee.objects.filter(patent_id=OuterRef("id"))
                .values("patent_id")
                .annotate(count=Count("patent_id"))
                .values("count"),
                output_field=IntegerField(),
            ),
            inventor_count=Subquery(
                Inventor.objects.filter(patent_id=OuterRef("id"))
                .values("patent_id")
                .annotate(count=Count("patent_id"))
                .values("count"),
                output_field=IntegerField(),
            ),
            incoming_citations_count=Subquery(
                PatentCitation.objects.filter(cited_patent_id=OuterRef("id"))
                .values("cited_patent_id")
                .annotate(count=Count("cited_patent_id"))
                .values("count"),
                output_field=IntegerField(),
            ),
            outgoing_citations_count=Subquery(
                PatentCitation.objects.filter(citing_patent_id=OuterRef("id"))
                .values("citing_patent_id")
                .annotate(count=Count("citing_patent_id"))
                .values("count"),
                output_field=IntegerField(),
            ),
        )
        print("Patent counts updated successfully!")

    def handle(self, *args, **options):
        self.handle_location()
        self.handle_cpc()
        self.handle_patent()
        self.handle_patent_cpc_group()
        self.handle_pct()
        self.handle_inventor()
        self.handle_assignee()
        self.handle_us_patent_citation()
        self.handle_foreign_citation()
        self.handle_counts()
