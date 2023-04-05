# PatentAnalyzer (under development)

PatentAnalyzer is a tool for analyzing patent data. It's written in Python and uses the Django framework. Its priority is to be easy to use and provide a good user interface. It's also designed to be easily extensible. 

# TODO

* Create the form (query builder)
    - Ensure that throttle is working
    - Try to do something about latency in field-model requests
* Index the tables (with goal of speeding up queries of the query builder and django-admin)
    - It's best if data is indexed after insertion
    - I could try Model.objects.db.create_index()
    - I could also try to use the Model.object.db.execute() - better for more complex queries (I will need full text indexes for patent.title and patent.abstract)
    