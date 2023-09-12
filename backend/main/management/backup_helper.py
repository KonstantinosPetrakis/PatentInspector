from os import system as _
from os import remove as rm
from io import StringIO
from contextlib import redirect_stderr, redirect_stdout
import sys

import requests as r
import gdown


def backup(database_name: str, backup_url1: str, backup_url2: str = None):
    """
    This function will load the entire database from a dump file.

    Args:
        database_name (str): The name of the database.
        backup_url (str): The URL of the backup file.
    """

    out = StringIO()
    err = StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        gdown.download(backup_url1, "dump")

    if "Access denied" in out.getvalue():
        if backup_url2 is None:
            print("Access denied to the file, Google Drive limits exceeded. Try again later.")
            exit(1)
        
        print("Access denied. Trying secondary URL...")
        res = r.get(backup_url2)
        with open("dump", "wb") as f:
            f.write(res.content)

    print("Database downloaded.")

    _(f"pg_restore -j 8 -d {database_name} dump")
    print("Database loaded.")

    rm("dump")
    print("Database dump file removed.")


if __name__ == "__main__":
    if len(sys.argv) not in [3, 4]:
        print("Usage: python backup_helper.py <database_name> <back_up_url1> <back_up_url2: optional>")
        exit(1)
    backup(*sys.argv[1:])
    