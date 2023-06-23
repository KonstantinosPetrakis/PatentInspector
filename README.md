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
python manage.py resetdb
python manage.py uspto
python manage.py index # not necessary but recommended
python manage.py runserver
```

### To-do
* Add random seed to topic modeling algorithms so they produce stable results. 
