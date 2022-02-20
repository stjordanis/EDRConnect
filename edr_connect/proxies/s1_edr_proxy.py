import datetime
import io
import secrets
import time
from http import HTTPStatus
from io import BytesIO
from typing import List
from typing import Optional
from typing import Tuple

import requests

from edr_connect.proxies.base_edr_proxy import AlertInfo
from edr_connect.proxies.base_edr_proxy import BaseEDRProxy
from edr_connect.proxies.base_edr_proxy import NoteInfo
from edr_connect.utils.base_url_session import BaseUrlSession
from edr_connect.utils.log import get_logger

_logger = get_logger()

ACTIVITIES_ROUTE = 'web/api/v2.1/activities'
THREATS_ROUTE = '/web/api/v2.1/threats'
FETCH_FILE_ROUTE = '/web/api/v2.1/threats/fetch-file'
DOWNLOAD_FILE_ROUTE = '/web/api/v2.1'
GET_NOTES_ROUTE = '/web/api/v2.1/threats/{}/notes'
SEND_NOTES_ROUTE = '/web/api/v2.1/threats/notes'


class S1EDRProxy(BaseEDRProxy):
    def fetch_latest_alerts(self, hours: int) -> List[AlertInfo]:
        hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
        response = self.get(THREATS_ROUTE,
                            params={'createdAt__gte': hours_ago.isoformat(), 'limit': 1000, 'sortOrder': 'desc'})
        return self.normalize_alerts_info(response.json()['data'])

    # Check if endpoint is offline
    def download_file(self, alert_id: str) -> Tuple[Optional[BytesIO], Optional[str]]:
        download_url, zip_password = self._fetch_file(alert_id)
        if not download_url:
            return None, None

        _logger.debug(f'downloading file from s1 (download url is: {download_url})')
        response = self.get(DOWNLOAD_FILE_ROUTE + download_url)
        _logger.debug(f'download finished')

        file = io.BytesIO(response.content)
        return file, zip_password

    def get_notes(self, alert_id: str) -> List[NoteInfo]:
        response = self.get(GET_NOTES_ROUTE.format(alert_id))
        return self.normalize_alert_notes(response.json()['data'])

    def send_note(self, alert_ids: List[str], note: str):
        self.post(SEND_NOTES_ROUTE,
                  json={'data': {'text': note}, 'filter': {'ids': alert_ids}})
        _logger.info(f'note sent for alerts {alert_ids}')

    def get_session(self) -> BaseUrlSession:
        headers = {'Authorization': f'ApiToken {self.api_key}'}
        session = BaseUrlSession(self.edr_base_address)
        session.headers = headers
        session.verify = self.ssl_verification
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
        return session

    @staticmethod
    def _format_error(error: dict) -> str:
        error_text = ''
        if 'title' in error:
            error_text = f'{error["title"]}'
        if 'details' in error:
            error_text = f'{error_text}: {error["details"]}'
        if 'code' in error:
            error_text = f'{error_text} (code:{error["code"]})'
        return error_text

    def assert_response(self, response: requests.Response):
        if response.status_code != HTTPStatus.OK:
            try:
                response_data = response.json()
                error_text = '\n'.join(self._format_error(error) for error in response_data['errors'])
            except Exception:
                error_text = f'Server returned {response.status_code} status code'

            _logger.error(error_text)
            raise RuntimeError(error_text)

    def _fetch_file(self, alert_id: str) -> Tuple[Optional[str], Optional[str]]:
        zip_password = secrets.token_urlsafe(32)
        fetch_file_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=5)

        _logger.debug('sending fetch command to the endpoint')
        self.post(FETCH_FILE_ROUTE,
                  json={'data': {'password': zip_password}, 'filter': {'ids': [alert_id]}})

        for count in range(self.file_download_num_of_retries):
            _logger.debug(f'waiting for s1 to fetch the file from the endpoint ({count}) for alert {alert_id}')
            time.sleep(self.file_download_timeout_in_seconds)
            response = self.get(ACTIVITIES_ROUTE,
                                params={'threatIds': alert_id,
                                        'activityTypes': 86,
                                        'createdAt__gte': fetch_file_time.isoformat()})
            data = response.json()

            for activity in data['data']:
                download_url = activity['data'].get('downloadUrl')
                if download_url:
                    return download_url, zip_password
        else:
            err_msg = ('Time out fetching the file, this is most likely when the endpoint is powered off '
                       'or the agent is shut down')

            _logger.error(err_msg)
            return None, None

    def normalize_alerts_info(self, alerts_info: List[dict]) -> List[AlertInfo]:
        return [AlertInfo(alert_info['id'],
                          (alert_info['threatInfo'].get('sha256') or
                           alert_info['threatInfo'].get('sha1') or
                           alert_info['threatInfo'].get('md5')),
                          alert_info['agentRealtimeInfo'].get('agentIsActive'),
                          alert_info['agentRealtimeInfo'].get('agentOsType')) for alert_info in alerts_info]

    def normalize_alert_notes(self, notes_info: List[dict]) -> List[NoteInfo]:
        return [NoteInfo(note_info['text']) for note_info in notes_info]
