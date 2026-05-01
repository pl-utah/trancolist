# Copyright 2026 The University of Utah
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys


class MissingCredentialsError(Exception):
    def __init__(self, email_is_none: bool, api_key_is_none: bool, cred_path: Path | None):
        msg = ""
        if cred_path is None:
            cred_path_msg = ""
        else:
            cred_path_msg = f" not in {cred_path}"

        if email_is_none:
            msg += f"Email was not found:{cred_path_msg} and envvar TRANCO_EMAIL was not set.\n"
        if api_key_is_none:
            msg += f"API key was not found:{cred_path_msg} and envvar TRANCO_API_KEY was not set.\n"
        super().__init__(msg)


@dataclass
class Credentials:
    email: str
    api_key: str


def load_credentials(cred_path: Path | None) -> Credentials:
    """
    Tries to load credentials from environment variables TRANCO_EMAIL and
    TRANCO_API_KEY first, then from the json file at `cred_path`.
    """
    json_email = None
    json_api_key = None
    if cred_path and cred_path.is_file():
        with open(cred_path) as f:
            creds = json.load(f)
            json_email = creds.get("email")
            json_api_key = creds.get("api_key")
    env_email = os.environ.get("TRANCO_EMAIL")
    env_api_key = os.environ.get("TRANCO_API_KEY")
    email = env_email if env_email is not None else json_email
    api_key = env_api_key if env_api_key is not None else json_api_key
    if (email is None) or (api_key is None):
        raise MissingCredentialsError(email is None, api_key is None, cred_path)
    return Credentials(email, api_key)