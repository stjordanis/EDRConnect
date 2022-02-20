import abc
from dataclasses import dataclass
from typing import List

import requests
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_fixed

default_retry = retry(
    wait=wait_fixed(0.5),
    retry=retry_if_exception_type(requests.ConnectionError),
    stop=stop_after_attempt(3),
    reraise=True)


@dataclass
class AlertInfo:
    alert_id: str
    file_hash: str
    is_agent_active: bool
    agent_os_type: str


@dataclass
class NoteInfo:
    text: str


class BaseEDRProxy:
    def __init__(self,
                 edr_base_address: str,
                 api_key: str,
                 ssl_verification: bool,
                 default_http_timeout_in_seconds: int,
                 file_download_num_of_retries: int,
                 file_download_timeout_in_seconds: int):
        self.api_key = api_key
        self.ssl_verification = ssl_verification
        self.edr_base_address = edr_base_address
        self.default_http_timeout_in_seconds = default_http_timeout_in_seconds
        self.file_download_num_of_retries = file_download_num_of_retries
        self.file_download_timeout_in_seconds = file_download_timeout_in_seconds
        self._session = self.get_session()

    @default_retry
    def get(self,
            url: str,
            params: dict = None,
            timeout_in_seconds=None,
            **kwargs) -> requests.Response:
        if timeout_in_seconds is None:
            timeout_in_seconds = self.default_http_timeout_in_seconds

        response = self._session.get(url, params=params, timeout=timeout_in_seconds, **kwargs)
        self.assert_response(response)
        return response

    @default_retry
    def post(self,
             url: str,
             data: dict = None,
             json: dict = None,
             timeout_in_seconds=None,
             **kwargs) -> requests.Response:
        if not timeout_in_seconds:
            timeout_in_seconds = self.default_http_timeout_in_seconds
        response = self._session.post(url, data=data, json=json, timeout=timeout_in_seconds, **kwargs)
        self.assert_response(response)
        return response

    @abc.abstractmethod
    def assert_response(self, response: requests.Response):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_session(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def fetch_latest_alerts(self, hours: int):
        raise NotImplementedError()

    @abc.abstractmethod
    def download_file(self, alert_id: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def send_note(self, alert_ids: List[str], note: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_notes(self, alert_id: str) -> List[dict]:
        raise NotImplementedError()

    @abc.abstractmethod
    def normalize_alerts_info(self, alerts_info: List[dict]) -> AlertInfo:
        raise NotImplementedError()

    @abc.abstractmethod
    def normalize_alert_notes(self, notes_info: List[dict]) -> List[NoteInfo]:
        raise NotImplementedError()
