# Copyright 2026 The University of Utah
# Copyright (c) 2020 Victor Le Pochat
# SPDX-License-Identifier: MIT

from core import Domain
from credentials import Credentials
from dataclasses import dataclass
import platform
import requests
from typing import Any, Iterator, Literal


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
    stream: Iterator[bytes]
    top_n: int | Literal['full']

    def id(self) -> str:
        return self.metadata['list_id']


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
                raise_other_status(response)    
                raise

    def request_email(self, email: str, list_id: str, list_size: int | Literal['full']):
        response = self.session.post(
            "https://tranco-list.eu/notify_email",
            data={
                "email": email,
                "list_id": list_id,
                "list_size": list_size,
            }
        )
        if response.status_code == 202:
            return
        raise_other_status(response)

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
                raise_other_status(response)
                raise

    def download_available(self, available: Available, top: int | Literal['full'] = 'full') -> TrancoList:
        download_url = available.download_url().removesuffix("/full")
        download_url = f"{download_url}/{top}"
        response = self.session.get(
            download_url,
            stream=True
        )
        if response.status_code == 200:
            return TrancoList(available.metadata, response.iter_lines(), top)
        raise_other_status(response)
        raise

    def download_if_available(self, metadata: MetadataResult, top: int | Literal['full'] = 'full') -> DownloadResult:
        match metadata:
            case InProgress(_) as in_progress:
                return in_progress
            case Available(_) as available:
                return self.download_available(available, top)


def parse_tranco_line(line: str) -> Domain:
    return Domain(line.split(',')[1])


def raise_other_status(response: requests.Response):
    response.raise_for_status()
    raise RuntimeError(f"Unexpected status code {response.status_code}", response)