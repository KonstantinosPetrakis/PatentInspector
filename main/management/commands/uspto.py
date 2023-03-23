"""
----------------------------------------------------------------------------------------------------
# What's this?
----------------------------------------------------------------------------------------------------
This module defines a command that downloads all the necessary data from the USPTO and inserts it to
the database.

It's execution takes about 3 hours on a decent computer and internet connection 
(~16GB RAM [I guess 10GB could also be enough] is required for it to run,
if you have less you should alter some of the code to use chunks)

----------------------------------------------------------------------------------------------------
# How does it work?
----------------------------------------------------------------------------------------------------
It uses pandas to preprocess the data.

For relatively small tables, it uses django's ORM bulk_create method to insert the data into the
database.

For larger tables, it uses the postgres_copy module to insert the data into the database.
"""


from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.conf import settings
from main.models import *
import zipfile
import requests as r
import pandas as pd
import numpy as np
import os


# Constant definitions and initial setup 
DATA_DIRECTORY = f"{settings.BASE_DIR}/main/data"
ENDPOINT = "https://s3.amazonaws.com/data.patentsview.org/download/"
os.makedirs(DATA_DIRECTORY, exist_ok=True)

location_id_map = {} # Will be used to map USPTO ids,
                     # to new generated IDs so relationships can be created.

patent_id_map = {} # Will be used to map USPTO ids to new generated IDs
                   # so relationships can be created.


class Command(BaseCommand):
    help = 'This command downloads all the necessary data from the USPTO and inserts it  \
        "into the database.'


    def download_and_unzip(self, table: str):
        """Downloads and unzips a table from the USPTO endpoint.

        Args:
            table (str): the name of the table to download and unzip.
        """

        res = r.get(f"{ENDPOINT}{table}.tsv.zip")
        with open(f"{DATA_DIRECTORY}/{table}.tsv.zip", "wb") as f:
            f.write(res.content)
        
        with zipfile.ZipFile(f"{DATA_DIRECTORY}/{table}.tsv.zip", "r") as z:
            z.extractall(DATA_DIRECTORY)
        os.remove(f"{DATA_DIRECTORY}/{table}.tsv.zip")


    def handle_location(self):
        global location_id_map

        # self.download_and_unzip("g_location_disambiguated")

        locations = pd.read_csv(f"{DATA_DIRECTORY}/g_location_disambiguated.tsv", sep="\t", 
            usecols=["location_id", "disambig_country", "disambig_state", "disambig_city", 
                "longitude", "latitude", "county_fips", "state_fips"],
            dtype={"location_id": str, "disambig_country": str, "disambig_state": str, 
                "disambig_city": str, "longitude": float, "latitude": float, "county_fips": "Int64",
                "state_fips": "Int64"})
        
        locations.rename(columns={"disambig_country": "country_code", "disambig_state": "state", 
            "disambig_city": "city"}, inplace=True)
        
        location_old_ids = locations["location_id"].copy()
        locations.drop(columns=["location_id"], inplace=True)

        locations["point"] = locations.apply(lambda x: Point(x["longitude"], x["latitude"]), axis=1)
        locations.drop(columns=["longitude", "latitude"], inplace=True)
        locations = locations.astype(object).replace(np.nan, None).to_dict("records")
        
        locations = [Location(**location) for location in locations]
        Location.objects.bulk_create(locations)

        for i in range(len(location_old_ids)):
            location_id_map[location_old_ids[i]] = locations[i].id

        # os.remove(f"{DATA_DIRECTORY}/g_location_disambiguated.tsv")


    def handle_cpc(self):
        # self.download_and_unzip("g_cpc_title")
        cpcs = pd.read_csv(f"{DATA_DIRECTORY}/g_cpc_title.tsv", sep="\t")

        # Create CPCClasses
        cpc_classes = cpcs.groupby("cpc_class", as_index=False)[["cpc_class_title"]].first()
        cpc_classes["section_id"] = cpc_classes["cpc_class"].str[0]
        cpc_classes = cpc_classes.rename(columns={"cpc_class": "_class", "cpc_class_title": "title"})
        cpc_classes = [CPCClass(**cpc_class) for cpc_class in cpc_classes.to_dict("records")]
        CPCClass.objects.bulk_create(cpc_classes)
  
        # Create CPCSubclasses
        cpc_subclasses = cpcs.groupby("cpc_subclass", 
            as_index=False)[["cpc_class", "cpc_subclass_title"]].first()
        cpc_subclasses = cpc_subclasses.rename(columns={"cpc_class": "_class_id",
            "cpc_subclass": "subclass", "cpc_subclass_title": "title"})
        cpc_subclasses = [CPCSubclass(**cpc_subclass) 
            for cpc_subclass in cpc_subclasses.to_dict("records")]
        CPCSubclass.objects.bulk_create(cpc_subclasses)

        # Create CPCGroups
        cpc_groups = cpcs[["cpc_group", "cpc_subclass", "cpc_group_title"]]
        cpc_groups = cpc_groups.rename(columns={"cpc_group": "group",
            "cpc_subclass": "subclass_id", "cpc_group_title": "title"})
        cpc_groups = [CPCGroup(**cpc_group) for cpc_group in cpc_groups.to_dict("records")]
        CPCGroup.objects.bulk_create(cpc_groups)

        # os.remove(f"{DATA_DIRECTORY}/g_cpc_title.tsv")


    def handle_patent(self):
        global patent_id_map

        # self.download_and_unzip("g_patent")
        # self.download_and_unzip("g_application")
        # self.download_and_unzip("g_figures")

        # Preprocess data
        patents = pd.read_csv(f"{DATA_DIRECTORY}/g_patent.tsv", sep="\t",
            usecols=lambda col: col not in ['wipo_kind', 'filename'], 
            dtype={"patent_id": str, "patent_type": str, "patent_date": str, "patent_title": str,
                "patent_abstract": str, "num_claims": "Int64", "withdrawn": bool})

        application = pd.read_csv(f"{DATA_DIRECTORY}/g_application.tsv", sep="\t",
            usecols=["patent_id", "filing_date"], dtype={"patent_id": str, "filing_date": str})
        patents = pd.merge(patents, application, on="patent_id", how="left")
        del application

        figures = pd.read_csv(f"{DATA_DIRECTORY}/g_figures.tsv", sep="\t",
            usecols=["patent_id", "num_figures", "num_sheets"], 
            dtype={"patent_id": str, "num_figures": "Int64", "num_sheets": "Int64"})
        patents = pd.merge(patents, figures, on="patent_id", how="left")
        del figures
        
        patents = patents.astype(object).replace(np.nan, None)
        patents = patents.rename(columns={"patent_id": "office_patent_id", 
                "patent_type": "type", "patent_date": "granted_date", "num_sheets": "sheets_count",
                "filing_date": "application_filed_date", "patent_title": "title",
                "patent_abstract": "abstract", "num_figures": "figures_count", 
                "num_claims": "claims_count"})
        patents["office"] = "USPTO"

        patent_id_map = dict(zip(patents["office_patent_id"], patents["id"]))

        patents.to_csv(f"{DATA_DIRECTORY}/g_patent_preprocessed.csv", index=False)
        del patents
        
        # Load data
        Patent.objects.from_csv(f"{DATA_DIRECTORY}/g_patent_preprocessed.csv")

        # os.remove(f"{DATA_DIRECTORY}/g_patent_preprocessed.csv")
        # os.remove(f"{DATA_DIRECTORY}/g_patent.tsv")
        # os.remove(f"{DATA_DIRECTORY}/g_application.tsv")
        # os.remove(f"{DATA_DIRECTORY}/g_figures.tsv")


    def handle_patent_cpc_group(self): 
        # self.download_and_unzip("g_cpc_current")

        # Preprocess data
        valid_cpcs = CPCGroup.objects.values_list("group", flat=True)

        patent_cpc_groups = pd.read_csv(f"{DATA_DIRECTORY}/g_cpc_current.tsv", sep="\t", 
            usecols=["patent_id", "cpc_group"], 
            dtype={"patent_id": str, "cpc_group": str})
        
        patent_cpc_groups = patent_cpc_groups.rename(columns={"cpc_group": "cpc_group_id"})
        patent_cpc_groups["patent_id"] = patent_cpc_groups["patent_id"].map(patent_id_map)
    
        # About 800 patents have invalid CPC groups, so we need to ignore them 
        patent_cpc_groups = patent_cpc_groups[patent_cpc_groups["cpc_group_id"].isin(valid_cpcs)]
        
        patent_cpc_groups.to_csv(f"{DATA_DIRECTORY}/g_cpc_current_preprocessed.csv", index=False)
        del patent_cpc_groups

        # Load data
        PatentCPCGroup.objects.from_csv(f"{DATA_DIRECTORY}/g_cpc_current_preprocessed.csv")

        # os.remove(f"{DATA_DIRECTORY}/g_cpc_current_preprocessed.csv")
        # os.remove(f"{DATA_DIRECTORY}/g_cpc_current.tsv")


    def handle_pct(self):
        # self.download_and_unzip("g_pct_data")

        pct_data = pd.read_csv(f"{DATA_DIRECTORY}/g_pct_data.tsv", sep="\t", usecols=["patent_id",
            "published_or_filed_date", "filed_country", "pct_doc_number", "pct_doc_type"],
            dtype={"patent_id": str, "published_or_filed_date": str, "filed_country": str,
                "pct_doc_number": str, "pct_doc_type": str})

        pct_data.rename(columns={"pct_doc_number": "pct_id", "pct_doc_type": "granted"}, inplace=True)
        
        pct_data["patent_id"] = pct_data["patent_id"].map(patent_id_map)
        pct_data["granted"] = pct_data["granted"].map({"wo_grant": True, "pct_application": False})
        pct_data = pct_data[pct_data["published_or_filed_date"].notna()]
        pct_data = pct_data.to_dict("records")

        PCTData.objects.bulk_create([PCTData(**pct) for pct in pct_data])

        # os.remove(f"{DATA_DIRECTORY}/g_pct_data.tsv")


    def handle_inventor(self):
        # self.download_and_unzip("g_inventor_disambiguated")

        # Preprocess data
        inventors_chunks = pd.read_csv(f"{DATA_DIRECTORY}/g_inventor_disambiguated.tsv", sep="\t",
            usecols=["patent_id", "location_id", "disambig_inventor_name_first",
                "disambig_inventor_name_last", "male_flag"],
            dtype={"patent_id": str, "location_id": str, "disambig_inventor_name_first": str, 
                "disambig_inventor_name_last": str, "male_flag": object}, chunksize=1000000)

        first_chunk = True
        for inventors_chunk in inventors_chunks:
            # Process chunk
            inventors_chunk = inventors_chunk.rename(columns=
                {"disambig_inventor_name_first": "first_name", 
                    "disambig_inventor_name_last": "last_name", "male_flag": "male"})
            
            inventors_chunk["patent_id"] = inventors_chunk["patent_id"].map(patent_id_map)
            inventors_chunk["location_id"] = inventors_chunk["location_id"].map(location_id_map)
            # There are some invalid location ids, so we need to remove them
            inventors_chunk = inventors_chunk[inventors_chunk["location_id"].notna()]
            inventors_chunk["location_id"] = inventors_chunk["location_id"].astype(int)
            inventors_chunk["male"] = inventors_chunk["male"].map({1.0: True, 0.0: False})
            
            # Store chunk
            if first_chunk: 
                inventors_chunk.to_csv(f"{DATA_DIRECTORY}/g_inventor_disambiguated_preprocessed.csv",
                    index=False, header=True, )
                first_chunk = False
            else:
                inventors_chunk.to_csv(f"{DATA_DIRECTORY}/g_inventor_disambiguated_preprocessed.csv",
                    mode="a", index=False, header=False)
        
        # Load data
        Inventor.objects.from_csv(f"{DATA_DIRECTORY}/g_inventor_disambiguated_preprocessed.csv")
        # os.remove(f"{DATA_DIRECTORY}/g_inventor_disambiguated.tsv")
        # os.remove(f"{DATA_DIRECTORY}/g_inventor_disambiguated_preprocessed.csv")


    def handle_assignee(self):
        pass


    def handle_patent_citation(self): # this is gonna be hard
        pass 


    def handle(self, *args, **options):
        global patent_id_map

        Inventor.objects.all().delete()
        Location.objects.all().delete()
        self.handle_location()   
        
        patent_id_map = {patent["office_patent_id"]: patent["id"] 
            for patent in Patent.objects.filter(office="USPTO").values("id", "office_patent_id")}

        self.handle_inventor()

        # Interesting tables:
        # https://patentsview.org/download/data-download-tables
        # https://patentsview.org/download/data-download-dictionary