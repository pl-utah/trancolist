# Copyright 2026 The University of Utah
# Copyright (c) 2020 Victor Le Pochat
# SPDX-License-Identifier: MIT

from credentials import Credentials
from dataclasses import dataclass
import platform
import requests
from typing import Any, Iterator 


@dataclass
class Available:
    metadata: dict[str, Any]
    
    def download_url(self) -> str:
        return self.metadata['download']


@dataclass
class InProgress:
    metadata: dict[str, Any]

    def id(self) -> str:
        return self.metadata['list_id']


@dataclass
class TrancoList:
    metadata: dict[str, Any]
    stream: Iterator[str]


MetadataResult = Available | InProgress


DownloadResult = TrancoList | InProgress


class AuthenticationError(Exception):
    def __init__(self):
        super().__init__("Invalid Credentials")


class TooManyRequests(Exception):
    def __init__(self):
        super().__init__("Another list is already being generated for your account.")


class Tranco:
    # Based on https://github.com/DistriNet/tranco-python-package/blob/main/tranco/tranco.py
    session: requests.Session

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Python/{} python-requests/{} trancolist'
                .format(platform.python_version(), requests.__version__)
        })

    def request_custom_list(self, creds: Credentials, config: dict[str, Any]) -> MetadataResult:
        response = self.session.put(
            "https://tranco-list.eu/api/lists/create",
            auth=(creds.email, creds.api_key),
            json=config
        )
        match response.status_code:
            case 200:
                return Available(response.json())
            case 202:
                return InProgress(response.json())
            case 400:
                raise ValueError("Invalid configuration.")
            case 401:
                raise AuthenticationError()
            case 429:
                raise TooManyRequests()
            case _:
                response.raise_for_status()
                raise
    
    def get_list_id(self, id: str) -> MetadataResult:
        response = self.session.get(f"https://tranco-list.eu/api/lists/id/{id}")
        match response.status_code:
            case 200:
                return Available(response.json())
            case 202:
                return InProgress(response.json())
            case 404:
                raise ValueError(f"List with ID {id} not found.")
            case _:
                response.raise_for_status()
                raise

    def download_available(self, available: Available, top: int | None = None) -> TrancoList:
        top_url = top if top is not None else "full"
        response = self.session.get(
            f"{available.download_url()}/{top_url}",
            stream=True
        )
        response.raise_for_status()
        return TrancoList(available.metadata, response.iter_lines())

    def download_if_available(self, metadata: MetadataResult, top: int | None = None) -> DownloadResult:
        match metadata:
            case InProgress(_):
                return metadata
            case Available(_):
                return self.download_available(metadata, top)