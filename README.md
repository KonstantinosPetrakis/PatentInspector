# PatentAnalyzer (under development)

PatentAnalyzer is a tool for analyzing patent data. It's written in Python and uses the Django framework. Its priority is to be easy to use and provide a good user interface. It's also designed to be easily extensible. 

# TODO
* Continue with USPTO data extraction (pct, assignee, inventor, and citation)
* Don't forget to use autocomplete_fields in the admin interface (speeds up the admin interface by a lot)
* Create the form (query builder) page
* Index the tables (with goal of speeding up queries of the query builder and django-admin)
    - It's best if data is indexed after insertion
    - I could try Model.objects.db.create_index()
    - I could also try to use the Model.object.db.execute() 