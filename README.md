# PatentAnalyzer (under development)

PatentAnalyzer is a tool for analyzing patent data. It's written in Python and uses the Django framework. Its priority is to be easy to use and provide a good user interface. It's also designed to be easily extensible. 

# TODO
* Try to optimize the database queries, the timings right now aren't acceptable.
* Create before/after indexing benchmarks (could be done via a management command automatically).
That management command would use the form and it's method, the result could be a csv.