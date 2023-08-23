import string
from multiprocessing import Pool
from typing import Iterable
from datetime import datetime

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive, GoogleDriveFile


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


def login_with_service_account() -> GoogleAuth:
    """
    This function logs in to Google Drive with a service account.

    Returns:
        GoogleAuth: The GoogleAuth instance.
    """

    # Define the settings dict to use a service account
    # We also can use all options available for the settings dict like
    # oauth_scope,save_credentials,etc.
    settings = {
                "client_config_backend": "service",
                "service_config": {
                    "client_json_file_path": "service-secrets.json",
                }
            }
    # Create instance of GoogleAuth
    gauth = GoogleAuth(settings=settings)
    # Authenticate
    gauth.ServiceAuth()
    return gauth


def create_pubic_folder(
    drive: GoogleDrive, folder_name: str = "patentanalyzer"
) -> GoogleDriveFile:
    """
    This function creates a public folder on Google Drive.

    Args:
        drive (GoogleDrive): The Google Drive service.
        folder_name (str, optional): The name of the folder. Defaults to "patentanalyzer".

    Returns:
        GoogleDriveFile: The created folder.
    """

    new_folder = drive.CreateFile(
        {
            "title": folder_name,
            "parents": [{"kind": "drive#fileLink", "id": "root"}],
            "mimeType": "application/vnd.google-apps.folder",
        }
    )
    new_folder.Upload()

    new_folder.auth.service.permissions().insert(
        fileId=new_folder["id"],
        body={"type": "anyone", "role": "reader"},
        supportsTeamDrives=True,
    ).execute(http=new_folder.http)

    return new_folder
