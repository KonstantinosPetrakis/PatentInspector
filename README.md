# PatentAnalyzer (under development)

PatentAnalyzer is a tool for analyzing patent data. It's written in Python and uses the Django framework. Its priority is to be easy to use and provide a good user interface. It's also designed to be easily extensible. 

# TODO
* Try to optimize the database queries, the timings right now aren't acceptable.
* Create before/after indexing benchmarks (could be done via a management command automatically).
That management command would use the form and it's method, the result could be a csv.

Some benchmarks made by hand using gin index and trigram similarity:
* frequency 252k, 68s
* cpu 19k, 6s
* pins 39k, 57s
* button 32k, 11s
* sensor 331k, 1m 6s
* water 310k, 52s
* sugar 10k, 1.7s
* led 1.27m, 2m 47s 

Same benchmarks using full text search and trigram:
* frequency 47k, 21s
* cpu, 18k, 7s
* pins, 2k, 2s
* button, 30k, 8s
* sensor 325k, 45s
* water 295k, 1m 8s 
* sugar 10k, 2s 
* led 150k, 36s

Without indexes at all 
* frequency 252k, 3m 5s
* cpu 19k, 40s 
* pins 40k, 22s 
* button 32k, 22s 
* sensor 331k, 22s 
* water 310k, 22s
* sugar 10k, 23s 
* led 1.27m, 21s 