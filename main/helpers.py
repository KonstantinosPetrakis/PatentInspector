from __future__ import unicode_literals
from django.db.models.functions import Cast
from django.db.models.aggregates import Avg, StdDev
from django.db.models import Aggregate, FloatField, IntegerField, Func, F, Q, fields
from main.models import *


cpc_section_titles = {record["section"]: record["title"] # That's used for appending the section title to the section code
    for record in CPCSection.objects.all().values("section", "title")}


class Median(Aggregate):
    """
    Calculates the median value of a field.
    """

    function = 'PERCENTILE_CONT'
    name = 'median'
    output_field = FloatField()
    template = '%(function)s(0.5) WITHIN GROUP (ORDER BY %(expressions)s)'


class WordCount(Func):
    """
    Calculates the number of words in a string.
    """

    function = 'CHAR_LENGTH'
    name = 'word_count'
    template = "(%(function)s(%(expressions)s) - CHAR_LENGTH(REPLACE(%(expressions)s, ' ', '')))"
    output_field = IntegerField()


class ToTimeStamp(Func):
    """
    Converts a date to a timestamp.
    """

    function = 'TO_TIMESTAMP'
    name = 'to_timestamp'
    template = "cast(extract(epoch from %(expressions)s) as bigint)"
    output_field = fields.IntegerField()


def date_difference_in_years(date1, date2):
    """
    Calculates the difference between two dates in years.

    Args:
        date1: The most recent date field.
        date2: The later date field
    Returns:
        The difference between the two dates in years.
    """

    return (ToTimeStamp(date1) - ToTimeStamp(date2)) / 31104000 # 31104000 seconds in a year


def calculate_statistics(field, function=None, display_name=None):
    """
    Creates a dict with queries to calculate the average, median, and standard deviation of a field.

    Args:
        field (str): The field to calculate the statistics for.
        function (function, optional): The function to apply to the field before calculating
        the statistics. Defaults to None.
        display_name (str, optional): The name of the field to be displayed (selected as in SQL).
        If not specified it's the same as the field name. 

    Returns:
        dict: A dict with the queries to calculate the average, median, and standard deviation of a field.
    """

    if display_name is None: display_name = field

    return {
        f"avg_{display_name}": Avg(field),
        f"med_{display_name}": Median(field),
        f"std_dev_{display_name}": StdDev(field),
    }   if function is None else {
            f"avg_{display_name}": Avg(function(field)),
            f"med_{display_name}": Median(function(field)),
            f"std_dev_{display_name}": StdDev(function(field)),
        }


def format_statistics(result):
    """
    This function formats the statistics calculated by calculate_statistics() into a dict.
    Essentially, it groups the statistics by field in a dict of dicts.

    Args:
        result: The result of the query containing the statistics.

    Returns:
        Dict[Dict]: The dict of dicts containing the statistics, the inner dict has 3 keys: avg, med, and std_dev.
    """

    statistical_fields = [field[4:] for field in result if field.startswith("avg_")]
    return {field: {
        "avg": result[f"avg_{field}"],
        "med": result[f"med_{field}"],
        "std_dev": result[f"std_dev_{field}"],
    } for field in statistical_fields}


def group_fields(results, key="year"):
    """
    This function groups the results by a key.

    Args:
        results (List[Dict]): The results are a list of dicts with 2 or 3 keys.
        key (str, optional): The key to be used to group by. Defaults to "year".

    Returns:
        Dict[Dict]: The results grouped by the key.
    """
    
    many_values = len(results[0]) > 2 # 2 means there's only one value and the key to group by

    # Simple case: only one value, just create a dict {key: value} instead of the given list [{key: value}, ...]
    if not many_values:
        value_field = next(filter(lambda field: field != key, results[0].keys()))
        return {record[key]: record[value_field] for record in results if record[key] is not None}

    # Complex case: multiple values, create a dict of key: {key: {vk1: vv1, ...}, ...}
    output = {}
    years = set()
    unique_key_values = set(record[key] for record in results if record[key] is not None)

    for key_value in unique_key_values:
        key_value_results = list(filter(lambda record: record.get(key, None) == key_value, results))
        for key_value_result in key_value_results: key_value_result.pop(key)
        output[key_value] = group_fields(key_value_results)
        years.update(output[key_value].keys())

    # Fill in missing years with 0
    for key_value in output:
        for year in years:
            if year not in output[key_value]: output[key_value][year] = 0 

    # Sort output by keys
    return {k: v for k, v in sorted(output.items(), key=lambda item: item[0])}


def string_is_empty(field):
    """
    This function creates a query to check if a string field is empty.
    """

    return Q(**{f"{field}__isnull": True}) | Q(**{f"{field}__in": [" ", ""]})


def append_title_to_cpc(cpc_dict):
    """
    This function changes the keys of a dict of CPC sections to include the section title.

    Args:
        cpc_dict (Dict): The dictionary with keys the CPC section codes.

    Returns:
        Dict: The updated dictionary with keys the CPC section codes and the section title.
    """
# cpc_section_titles = {record["section"]: record["title"] # That's used for appending the section title to the section code
#     for record in CPCSection.objects.all().values("section", "title")}
    
    cpc_levels = list(cpc_dict.keys())
    cpc_level_len = len(cpc_levels[0])

    if cpc_level_len == 1: 
        return {f"{key} - {cpc_section_titles[key]}": value for key, value in cpc_dict.items()}
    elif cpc_level_len == 3:
        cpc_class_titles = {record["_class"]: record["title"] 
            for record in CPCSubclass.objects.filter(_class__in=cpc_levels).values("_class", "title")}
        return {f"{key} - {cpc_class_titles[key]}": value for key, value in cpc_dict.items()}
    elif cpc_level_len == 4:
        cpc_subclass_titles = {record["subclass"]: record["title"]
            for record in CPCGroup.objects.filter(subclass__in=cpc_levels).values("subclass", "title")}
        return {f"{key} - {cpc_subclass_titles[key]}": value for key, value in cpc_dict.items()}
    else:
        cpc_group_titles = {record["group"]: record["title"]
            for record in CPCGroup.objects.filter(group__in=cpc_levels).values("group", "title")}
        return {f"{key} - {cpc_group_titles[key]}": value for key, value in cpc_dict.items()}
        
