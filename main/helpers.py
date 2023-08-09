from typing import Iterable, Any
from collections import defaultdict
from functools import reduce
import operator

from django.db.models.aggregates import Avg, StdDev, Min, Max
from django.db.models import Aggregate, Func, fields
import tomotopy as tp


class Median(Aggregate):
    """
    Calculates the median value of a field.
    """

    function = "PERCENTILE_CONT"
    name = "median"
    output_field = fields.FloatField()
    template = "%(function)s(0.5) WITHIN GROUP (ORDER BY %(expressions)s)"


def calculate_statistics(field, display_name=None):
    """
    Creates a dict with queries to calculate the average, median, and standard deviation of a field.

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


def format_statistics(result):
    """
    This function formats the statistics calculated by calculate_statistics() into a dict.
    Essentially, it groups the statistics by field in a dict of dicts.

    Args:
        result: The result of the query containing the statistics.

    Returns:
        Dict[Dict]: The dict of dicts containing the statistics, the inner dict has 3 keys:
        avg, med, and std_dev.
    """

    fields = [field[4:] for field in result if field.startswith("avg_")]
    return {
        field: {
            "avg": result[f"avg_{field}"],
            "med": result[f"med_{field}"],
            "std_dev": result[f"std_dev_{field}"],
            "min": result[f"min_{field}"],
            "max": result[f"max_{field}"],
        }
        for field in fields
    }


def get_coordinates(field):
    """
    This function creates a query to get the coordinates of a point field.
    """

    return {
        "lng": Func(field, function="ST_X", output_field=fields.FloatField()),
        "lat": Func(field, function="ST_Y", output_field=fields.FloatField()),
    }


def group_fields(results: Iterable[dict], fields: list) -> dict:
    """
    This function groups the results of a query by the specified fields.

    Args:
        results (Iterable[dict]): The results of a query.
        fields (list): The fields to group by.

    Returns:
        dict: The results grouped by the specified fields.
    """

    # https://stackoverflow.com/a/59039243/11718554
    def ddict() -> defaultdict:
        """
        This function creates a defaultdict of defaultdicts.
        It allows 'infinite' nesting of defaultdicts.

        Returns:
            defaultdict: A defaultdict of defaultdicts.
        """

        return defaultdict(ddict)

    # https://stackoverflow.com/a/26496899
    def ddict_to_dict(d: defaultdict) -> dict:
        """
        This function converts a defaultdict of defaultdicts to a dict.

        Args:
            d (defaultdict): The defaultdict to convert.

        Returns:
            dict: The converted defaultdict.
        """

        if isinstance(d, defaultdict):
            d = {k: ddict_to_dict(v) for k, v in d.items()}
        return d

    # https://stackoverflow.com/a/14692747
    def getFromDict(dataDict: dict, mapList: list) -> Any:
        """
        This function gets a value from a dict using a list of keys.

        Args:
            dataDict (dict): The dict to get the value from.
            mapList (list): The list of keys to use.

        Returns:
            Any: The value from the dict.
        """

        return reduce(operator.getitem, mapList, dataDict)

    def setInDict(dataDict: dict, mapList: list, value: Any):
        """
        This function sets a value in a dict using a list of keys.

        Args:
            dataDict (dict): The dict to set the value in.
            mapList (list): The list of keys to use.
            value (Any): The value to set.
        """

        getFromDict(dataDict, mapList[:-1])[mapList[-1]] = value

    grouped_data = ddict()
    value_fields = list(set(results[0].keys() - set(fields)))
    single_value = len(value_fields) == 1

    for result in results:
        keys = [result[field] for field in fields]
        
        if any(key is None for key in keys):
            continue
        
        values = (
            result[value_fields[0]]
            if single_value
            else {field: result[field] for field in value_fields}
        )

        setInDict(grouped_data, keys, values)

    return ddict_to_dict(grouped_data)


def format_topic_analysis_results_sklearn(model, feature_names, n_top_words):
    """
    This function formats the results of a topic analysis model when sklearn is used.
    """

    # Check https://scikit-learn.org/stable/auto_examples/applications/plot_topics_extraction_with_nmf_lda.html

    topics = []
    for topic in model.components_:
        top_features_ind = topic.argsort()[: -n_top_words - 1 : -1]
        top_features = [feature_names[i] for i in top_features_ind]
        weights = topic[top_features_ind]
        topics.append({"words": top_features, "weights": weights.tolist()})
    return {"topics": topics, "coherence": "N/A"}


def format_topic_analysis_results_tomotopy(model, n_top_words):
    """
    This function formats the results of a topic analysis model when tomotopy is used.
    """

    topics = []
    for k in range(model.k):
        topic_words = model.get_topic_words(k, top_n=n_top_words)
        topics.append(
            {
                "words": [word for word, _ in topic_words],
                "weights": [weight for _, weight in topic_words],
            }
        )
    return {
        "topics": topics,
        "coherence": f"{tp.coherence.Coherence(model, coherence='c_v', top_n=n_top_words).get_score():.3f}",
    }
