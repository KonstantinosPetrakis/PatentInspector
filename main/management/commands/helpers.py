import string
from multiprocessing import Pool
from typing import Iterable
from datetime import datetime

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("wordnet", quiet=True)
lemma = WordNetLemmatizer()


def lemma_text(text: str | None) -> tuple[int, str]:
    """
    This function lemmatizes the text and returns the word count and the lemmatized text.
    Moreover it removes all stopwords.

    Args:
        text (str | None): The text to lemmatize.

    Returns:
        tuple[int, str]: The word count and the lemmatized text.
    """

    if not text:
        return 0, ""
    tokens = [
        lemma.lemmatize(w)
        for w in word_tokenize(text.lower().translate(str.maketrans("", "", string.punctuation)))
        if w not in stopwords.words("english")
    ]
    return len(tokens) - tokens.count("."), " ".join(tokens)


def multiprocessing_apply(iterable: Iterable, func: callable, processes=8) -> list:
    """
    This function applies a function to an iterable in parallel.

    Args:
        iterable (Iterable): The iterable to apply the function to.
        func (callable): The function to apply.
        processes (int, optional): The processes to use. Defaults to 8.

    Returns:
        list: The result of the function applied to the iterable.
    """

    pool = Pool(processes)
    data = pool.map(func, iterable)
    pool.close()
    pool.join()
    return data


def string_to_timestamp(string: str) -> float | None:
    """
    This function converts a string to a timestamp.

    Args:
        string (str): The string to convert.

    Returns:
        float | None: The timestamp.
    """

    return datetime.strptime(string, "%Y-%m-%d").timestamp()
