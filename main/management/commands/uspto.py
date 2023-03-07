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
location_id_map = {} # Will be used to map USPTO ids, to new generated IDs so relationships can be created.


class Command(BaseCommand):
    help = 'This command downloads all the necessary data from the USPTO and inserts it into the database.'


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
        locations = locations.astype(object).replace(np.nan, None)
        locations = locations.to_dict("records")

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
        cpc_classes = list(cpcs["cpc_class"].unique())
        cpc_subclasses = list(cpcs["cpc_subclass"].unique())
        cpc_groups = list(cpcs["cpc_group"].unique())

        # Create CPCClasses
        for i, cpc_class in enumerate(cpc_classes):
            cpc_class_first_row = cpcs.loc[cpcs["cpc_class"] == cpc_class].iloc[0]
            cpc_classes[i] = CPCClass(
                section=CPCSection.objects.get(section__startswith=cpc_class_first_row["cpc_class"][0]),
                _class=cpc_class,
                title=cpc_class_first_row["cpc_class_title"],
            )
        CPCClass.objects.bulk_create(cpc_classes)
  

        # Create CPCSubclasses
        for i, cpc_subclass in enumerate(cpc_subclasses):
            cpc_subclass_first_row = cpcs.loc[cpcs["cpc_subclass"] == cpc_subclass].iloc[0]
            cpc_subclasses[i] = CPCSubclass(
                _class=CPCClass.objects.get(_class=cpc_subclass_first_row["cpc_class"]),
                subclass=cpc_subclass,
                title=cpc_subclass_first_row["cpc_subclass_title"],
                )
        CPCSubclass.objects.bulk_create(cpc_subclasses)

        # Create CPCGroups
        

    def handle_patent(self):
        # self.download_and_unzip("g_patent")
        patents = pd.read_csv(f"{DATA_DIRECTORY}/patent.tsv", sep="\t")
        patents = patents.astype(object).replace(np.nan, None)
        patents = patents.to_dict("records")

        for i, patent in enumerate(patents):
            patent["location_id"] = location_id_map[patent["location_id"]]
            patents[i] = Patent(
                office="USPTO",
                office_patent_id=patent["patent_id"],
                type=patent["patent_type"],
            )
        # Patent.objects.bulk_create(patents)

    def handle(self, *args, **options):
        # self.handle_location()
        # self.handle_patent()
        # Location.objects.all().delete()

        CPCClass.objects.all().delete()
        CPCSubclass.objects.all().delete()
        self.handle_cpc()
        
        # Interesting tables:
        # https://patentsview.org/download/data-download-tables
        # https://patentsview.org/download/data-download-dictionary
        # https://s3.amazonaws.com/community.patentsview.org/PatentsView+Data+Logic+Diagram+FINAL.jpg