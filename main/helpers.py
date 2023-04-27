from __future__ import unicode_literals
from django.db.models.functions import Cast
from django.db.models import Aggregate, FloatField, IntegerField, Func, F, fields
from django.db import connection


class Median(Aggregate):
    function = 'PERCENTILE_CONT'
    name = 'median'
    output_field = FloatField()
    template = '%(function)s(0.5) WITHIN GROUP (ORDER BY %(expressions)s)'


class WordCount(Func):
    function = 'CHAR_LENGTH'
    name = 'word_count'
    template = "(%(function)s(%(expressions)s) - CHAR_LENGTH(REPLACE(%(expressions)s, ' ', '')))"
    output_field = IntegerField()


class ToTimeStamp(Func):
    function = 'TO_TIMESTAMP'
    name = 'to_timestamp'
    template = "cast(extract(epoch from %(expressions)s) as bigint)"
    output_field = fields.IntegerField()


def date_difference_in_years(date1, date2):
    return (ToTimeStamp(date1) - ToTimeStamp(date2)) / 31104000 # 31104000 seconds in a year