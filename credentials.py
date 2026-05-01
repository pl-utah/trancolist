# Copyright 2026 The University of Utah
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys


@dataclass
class Credentials:
    email: str
    api_key: str


def load_credentials(cred_path: Path | None) -> Credentials:
    """
    Tries to load credentials from environment variables TRANCO_EMAIL and
    TRANCO_API_KEY first, then from the json file at `cred_path`.
    """
    creds: dict[str, str | None] = { "email": None, "api_key": None }
    if cred_path and cred_path.is_file():
        with open(cred_path) as f:
            creds.update(json.load(f))
    env_email = os.environ.get("TRANCO_EMAIL")
    env_api_key = os.environ.get("TRANCO_API_KEY")
    email, api_key = creds["email"], creds["api_key"]
    if env_email:
        email = env_email
    if env_api_key:
        api_key = env_api_key
    if not email:
        print(f"Email was not found: not in {cred_path} and envvar TRANCO_EMAIL was not set.", file=sys.stderr)
    if not api_key:
        print(f"API Key was not found: not in {cred_path} and envvar TRANCO_API_KEY was not set.", file=sys.stderr)
    if not (email and api_key):
        sys.exit(1)
    return Credentials(email, api_key)