from typing import Iterable, Any
from itertools import groupby

from django.db.models.aggregates import Avg, StdDev, Min, Max
from django.db.models import Aggregate, Func, fields
import tomotopy as tp

from main.models import *


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


counter = 0


def group_fields(
    results: Iterable[dict], field1: str, field2: str = ""
) -> dict[dict | Any]:
    """
    This function groups the results of a query by two fields.

    Args:
        results (Iterable[dict]): The results of a query.
        field1 (str): The first field to group by.
        field2 (str, optional): The second field to group by. Defaults to "".

    Returns:
        dict[dict | Any]: A dict with the results grouped by the field(s).
    """

    def pop_and_return_dict(d: dict, key: Any) -> dict | Any:
        d.pop(key)
        return d.popitem()[1] if len(d) == 1 else d

    # Simple case where there is only one field
    if not field2:
        return {
            key: pop_and_return_dict(next(results), field1)
            for key, results in groupby(results, lambda x: x[field1])
            if key is not None
        }

    # Case where there are two fields
    return {
        key: group_fields(
            [pop_and_return_dict(result, field1) for result in results], field2
        )
        for key, results in groupby(results, lambda x: x[field1])
        if key is not None
    }


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
