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

Optimization ideas:
* Remove as many conditions as possible from fetch_representation of patents

* Create extra fields for precomputed values in Patent model:
    * Years to get granted
    * Title
    * Stemmed title
    * Title word count
    * Stemmed title count
    * Abstract word count without stemming
    * Abstract word count with stemming
    * Abstract stemmed instead of abstract
    * CPC group count
    * Inventor count
    * Assignee count
    * Incoming citation count
    * Outgoing citation count
    * Granted year extracted from date and indexed

* Create extra fields for precomputed values in Citation model:
    * Remove record name
    * Reference year extracted from date and indexed
    * Add representation field

* Create extra fields for precomputed values in Assignee model:
    * is_corporation

* Maybe use table joins instead of substring in cpc in entity info

