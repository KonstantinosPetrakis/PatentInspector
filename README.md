# PatentAnalyzer

PatentAnalyzer is a tool for analyzing patent data. It's written in Python and uses the Django framework. Its priority is to be easy to use and provide a good user interface. It's also designed to be easily extensible. 

## Run for development in debian based systems
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env # fill in the values (use DJANGO_DEBUG=False)
# Create the postgres database and user and install postgis and pg_trgm extensions
# In case the back up file is not available you can use the uspto and index commands manually.
python manage.py load_database
python manage.py runserver
```

## Run using docker (suitable for production)
```bash
cp .env.example .env
docker-compose up
```


# Todo
* Add date filtering in uspto management command so it is between 1836 and current year