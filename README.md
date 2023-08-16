# PatentAnalyzer

PatentAnalyzer is a tool for analyzing patent data. It's written in Python and uses the Django framework. Its priority is to be easy to use and provide a good user interface. It's also designed to be easily extensible. 

## Installation - run locally (for debian based systems)
```bash
git clone git@github.com:KonstantinosPetrakis/patent-analysis.git
cd patent-analysis
sudo ./ubuntu-requirements.sh
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
cp .env.example .env # fill in the .env file (you must create a postgres db and install the trigram extension)
psql -c "CREATE DATABASE patentanalyzer;"
python manage.py resetdb
python manage.py uspto
python manage.py index
python manage.py runserver
```

In the upcoming versions there will be a database dump in the cloud and a docker image for easier installation. So running commands like `python manage.py uspto` will not be necessary.
This is going to be especially useful when multiple offices are supported and the number of scripts that need to be run will increase.


# Todo
* Input the numbers topics for topic analysis and other options
* Tabs for descriptive analysis (per entities) - biblioshiny
* Add tables pane for plots and export options
* Add date filtering in uspto management command so it is between 1836 and current year
* Write back up and restore scripts
* Allow deployment through docker