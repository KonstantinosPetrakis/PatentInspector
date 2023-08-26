# PatentAnalyzer

PatentAnalyzer is a tool for analyzing patent data. It's written in Python and uses the Django framework. Its priority is to be easy to use and provide a good user interface. It's also designed to be easily extensible. 

You can use PatentAnalyzer in the following URL, please note that our resources are limited: https://patentanalyzer.csd.auth.gr/

## Run for development (postgis has dependencies varying by OS)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env # fill in the values (use DJANGO_DEBUG=False)
# Create the postgres database and user and install postgis and pg_trgm extensions.
# In case the back up file is not available you can use the resetdb, uspto and index commands manually
# in this particular order to create the database from scratch.
python manage.py load_database
python manage.py runserver
```

## Run using docker (suitable for production)
```bash
cp .env.example .env
docker-compose up
```
