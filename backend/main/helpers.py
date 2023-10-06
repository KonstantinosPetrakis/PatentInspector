from typing import Any, Iterable, List, Dict
import json

from django.db.models import Q, QuerySet
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Aggregate, fields
from django.db.models.aggregates import Avg, StdDev, Min, Max


class Median(Aggregate):
    """
    Calculates the median value of a field.
    """

    function = "PERCENTILE_CONT"
    name = "median"
    output_field = fields.FloatField()
    template = "%(function)s(0.5) WITHIN GROUP (ORDER BY %(expressions)s)"


def remove_redundant_cpc_entities(data):
    """
    Remove redundant keywords from the lower levels of the hierarchy for each level of the CPC.
    For example if the user selected A01 we don't need to include A01B, A01C, etc.

    Args:
        data: The data dictionary containing the CPC keywords.
    """

    hierarchies = ["cpc_section", "cpc_class", "cpc_subclass", "cpc_group"]
    for level_index, level in enumerate(hierarchies):
        for hierarchy_below in hierarchies[level_index + 1 :]:
            for key in data[level]:
                data[hierarchy_below] = [
                    keyword
                    for keyword in data[hierarchy_below]
                    if not keyword.startswith(key)
                ]


def exact_query(field: str, value: Any) -> Q:
    """
    Create an exact query for the given field and value.

    Args:
        field (str): The name of the field.
        value (Any): The value of the field.

    Returns:
        Q: The database query.
    """

    return Q(**{field: value}) if value else Q()


def range_query(field: str, value: Any) -> Q:
    """
    Create a range query for the given field and value.

    Args:
        field (str): The name of the field.
        value (Any): The value of the field.

    Returns:
        Q: The database query.
    """

    return Q(**{f"{field}__contained_by": value}) if value else Q()


def list_iregex_query(field: str, value: Iterable) -> Q:
    """
    Create a query containing any of the given values for the given field.

    Args:
        field (str): The name of the field.
        value (Iterable): The values of the field.

    Returns:
        Q: The database query.
    """

    return (
        Q(**{f"{field}__iregex": f"^({'|'.join(value)})"})
        if value not in [None, []]
        else Q()
    )


def location_query(field: str, location: Dict | None) -> Q:
    """
    Create a location query for the given field and value.

    Args:
        field (str): The name of the field.
        location (Dict | None): A dictionary containing the attributes lat, lng and radius.

    Returns:
        Q: The database query.
    """

    return (
        Q(
            **{
                f"{field}__distance_lte": (
                    Point(location["lng"], location["lat"]),
                    D(m=location["radius"]),
                )
            }
        )
        if location
        else Q()
    )


def format_statistics(result: QuerySet) -> List[List]:
    """
    This function formats the statistics for the given result in a tabular format.

    Args:
        result (QuerySet): The result to format.

    Returns:
        List[List]: The formatted result.
    """

    fields = [field[4:] for field in result if field.startswith("avg_")]
    tabular_result = [
        ["Variable", "Average", "Median", "Standard Deviation", "Minimum", "Maximum"]
    ]

    for field in fields:
        tabular_result.append(
            [
                field.replace("_", " ").title(),
                result[f"avg_{field}"],
                result[f"med_{field}"],
                result[f"std_dev_{field}"],
                result[f"min_{field}"],
                result[f"max_{field}"],
            ]
        )

    return tabular_result


def construct_statistics(field, display_name=None):
    """
    Constructs a dict with queries to calculate the average, median, and standard deviation of a field.

    Args:
        field (str): The field to calculate the statistics for.
        display_name (str, optional): The name of the field to be displayed.
        If not specified it's the same as the field name.

    Returns:
        dict: A dict with the queries to calculate the average, median, and standard deviation of a field.
    """

    if display_name is None:
        display_name = field

    return {
        f"avg_{display_name}": Avg(field),
        f"med_{display_name}": Median(field),
        f"std_dev_{display_name}": StdDev(field),
        f"min_{display_name}": Min(field),
        f"max_{display_name}": Max(field),
    }