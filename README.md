# PatentAnalyzer (under development)

PatentAnalyzer is a tool for analyzing patent data. It's written in Python and uses the Django framework. Its priority is to be easy to use and provide a good user interface. It's also designed to be easily extensible. 

# TODO
* Build query from the form
* Index the tables
    - Could try to use Model.objects.db.create_index() or Model.objects.db.execute()
    - Full text indexes for patent.title and patent.abstract would be good
    