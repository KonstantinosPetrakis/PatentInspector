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
        # self.download_and_unzip("g_location_disambiguated")
        locations = pd.read_csv(f"{DATA_DIRECTORY}/g_location_disambiguated.tsv", sep="\t")
        locations = locations.astype(object).replace(np.nan, None).to_dict("records")

        for i, location in enumerate(locations):
            location_id_map[location["location_id"]] = None
            locations[i] = Location(
                country_code=location["disambig_country"],
                state=location["disambig_state"],
                city=location["disambig_city"],
                point=Point(location["longitude"], location["latitude"]),
                county_fips=location["county_fips"],
                state_fips=location["state_fips"],
            )
        Location.objects.bulk_create(locations)

        for id, location in zip(location_id_map, locations):
            location_id_map[id] = location.id


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


    def handle_patent(self): # takes about 30m to run (without downloading data)
        # self.download_and_unzip("g_patent")
        # self.download_and_unzip("g_application")
        # self.download_and_unzip("g_figures")

        patent_chunks = pd.read_csv(f"{DATA_DIRECTORY}/g_patent.tsv", sep="\t",
            usecols=lambda col: col not in ['wipo_kind', 'filename'], 
            dtype={"patent_id": str, "patent_type": str, "patent_date": str, "patent_title": str,
                "patent_abstract": str, "num_claims": int, "withdrawn": bool}, chunksize=100000)
        
        application = pd.read_csv(f"{DATA_DIRECTORY}/g_application.tsv", sep="\t",
            usecols=["patent_id", "filing_date"], dtype={"patent_id": str, "filing_date": str})

        figures = pd.read_csv(f"{DATA_DIRECTORY}/g_figures.tsv", sep="\t",
            usecols=["patent_id", "num_figures", "num_sheets"], 
            dtype={"patent_id": str, "num_figures": int, "num_sheets": int})
        
        application_figures = pd.merge(application, figures, on="patent_id", how="left") 

        for patent_chunk in patent_chunks:
            patent_chunk = pd.merge(patent_chunk, application_figures, on="patent_id", how="left")
            patent_chunk = patent_chunk.astype(object).replace(np.nan, None)

            patent_chunk = patent_chunk.rename(columns={"patent_id": "office_patent_id", 
                "patent_type": "type", "patent_date": "granted_date", "num_sheets": "sheets_count",
                "filing_date": "application_filed_date", "patent_title": "title",
                "patent_abstract": "abstract", "num_figures": "figures_count", 
                "num_claims": "claims_count"})
            
            patent_chunk["office"] = "USPTO"
            Patent.objects.bulk_create([Patent(**patent) for patent in patent_chunk.to_dict("records")])


    def handle_patent_cpc_group(self):
        patent_id_map = {patent["office_patent_id"]: patent["id"] 
            for patent in Patent.objects.filter(office="USPTO").values("id", "office_patent_id")}
        patent_cpc_groups_chunks = pd.read_csv(f"{DATA_DIRECTORY}/g_cpc_current.tsv", sep="\t", 
            usecols=["patent_id", "cpc_group"], 
            dtype={"patent_id": str, "cpc_group": str}, chunksize=1000000)
        
        for patent_cpc_groups_chunk in patent_cpc_groups_chunks:
            patent_cpc_groups_chunk = patent_cpc_groups_chunk.rename(
                columns={"cpc_group": "cpc_group_id"})
        
            patent_cpc_groups_chunk["patent_id"] = patent_cpc_groups_chunk["patent_id"].map(patent_id_map)

            PatentCPCGroup.objects.bulk_create(PatentCPCGroup(**patent_cpc_group)
                for patent_cpc_group in patent_cpc_groups_chunk.to_dict("records"))
        

    def handle_pct_data(self):
        pass


    def handle_assignee(self):
        pass


    def handle_inventor(self):
        pass


    def handle_patent_citation(self): # this is gonna be hard
        pass 


    def handle(self, *args, **options):
        # self.handle_location()
        # self.handle_cpc()
        self.handle_patent()
        # self.handle_patent_cpc_group()
        
        # Interesting tables:
        # https://patentsview.org/download/data-download-tables
        # https://patentsview.org/download/data-download-dictionary