import datetime
import time
from enum import Enum
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from intezer_sdk import api
from intezer_sdk.analysis import Analysis
from intezer_sdk.analysis import get_latest_analysis
from intezer_sdk.api import get_global_api
from intezer_sdk.errors import HashDoesNotExistError
from intezer_sdk.util import get_analysis_summary
from requests import HTTPError

from edr_connect.proxies.base_edr_proxy import AlertInfo
from edr_connect.proxies.s1_edr_proxy import S1EDRProxy
from edr_connect.utils.log import get_logger

_logger = get_logger()


class EDRType(Enum):
    S1 = 'S1'


EDR_TYPE_TO_MANAGER = {EDRType.S1: S1EDRProxy}
SUPPORTED_OS_TYPE = ['windows', 'linux']


class AnalysisManager:
    def __init__(self,
                 edr_api_key: str,
                 analyze_api_key: str,
                 edr_base_address: str,
                 edr_type: EDRType,
                 ssl_verification: bool,
                 latest_analysis_limit_in_days: int,
                 latest_edr_alerts_in_hours: int,
                 cooldown_between_runs_in_minutes: int,
                 default_http_timeout_in_seconds: int,
                 file_download_num_of_retries: int,
                 file_download_timeout_in_seconds: int):
        self.edr_api_key = edr_api_key
        self.ssl_verification = ssl_verification
        self.edr_base_address = edr_base_address
        self.edr_type = edr_type
        self.analyze_api_key = analyze_api_key
        self.latest_analysis_limit_in_days = latest_analysis_limit_in_days
        self.latest_edr_alerts_in_hours = latest_edr_alerts_in_hours
        self.cooldown_between_runs_in_minutes = cooldown_between_runs_in_minutes
        self.default_http_timeout_in_seconds = default_http_timeout_in_seconds
        self.file_download_num_of_retries = file_download_num_of_retries
        self.file_download_timeout_in_seconds = file_download_timeout_in_seconds

        self.edr_proxy = EDR_TYPE_TO_MANAGER.get(edr_type)(self.edr_base_address,
                                                           self.edr_api_key,
                                                           self.ssl_verification,
                                                           self.default_http_timeout_in_seconds,
                                                           self.file_download_num_of_retries,
                                                           self.file_download_timeout_in_seconds)
        self.assert_vars()

        api.set_global_api(self.analyze_api_key)
        self.handled_alerts = set()
        self.running_analysis_id_and_alert_ids_by_hash: Dict[str, Tuple[int, set]] = {}
        self.handled_alerts_count = 0
        self.finished_analyses_count = 0
        self._exceptions = []

    def assert_vars(self):
        if not self.analyze_api_key:
            raise ValueError('INTEZER_API_KEY variable not set')
        if not self.edr_api_key:
            raise ValueError('EDR_API_KEY variable not set')
        if not self.edr_base_address:
            raise ValueError('EDR_BASE_ADDRESS variable not set')
        if not self.edr_type:
            raise ValueError('INTEZER_EDR_TYPE variable not set')
        if not self.edr_proxy:
            raise ValueError('Wrong INTEZER_EDR_TYPE environment variable value')

    def _should_skip(self, alert_info: AlertInfo) -> bool:
        if alert_info.agent_os_type not in SUPPORTED_OS_TYPE:
            return True

        if not alert_info.file_hash:
            _logger.debug(f'Alert {alert_info.alert_id} has no file hash')
            return True

        if alert_info.alert_id in self.handled_alerts:
            _logger.debug(f'Alert {alert_info.alert_id} already handled, skipping')
            return True

        if alert_info.file_hash in self.running_analysis_id_and_alert_ids_by_hash:
            _logger.debug(
                f'Alert {alert_info.alert_id} currently being analyzed skipping (hash: {alert_info.file_hash})')
            self._add_alert_to_running_analysis(alert_info.file_hash, alert_info.alert_id)
            return True

        return False

    def _add_alert_to_running_analysis(self, file_hash: str, alert_id: str):
        analysis_id, alert_ids = self.running_analysis_id_and_alert_ids_by_hash[file_hash]
        alert_ids.add(alert_id)
        self.running_analysis_id_and_alert_ids_by_hash[file_hash] = (analysis_id, alert_ids)

    def analyze_by_file(self, alert_info: AlertInfo) -> Optional[Analysis]:
        if not alert_info.is_agent_active:
            _logger.info('agent is offline, cannot download, skipping')
            return None

        analysis = None
        try:
            file, zip_password = self.edr_proxy.download_file(alert_info.alert_id)
            if file:
                analysis = Analysis(file_stream=file, file_name=f'{alert_info.alert_id}.zip', zip_password=zip_password)
        except Exception as ex:
            self.handle_exception(ex)

        return analysis

    def send_summary_report(self):
        summary_report = {'finished_analyses_count': self.finished_analyses_count,
                          'handled_alerts_count': self.handled_alerts_count}
        if self._exceptions:
            summary_report['exceptions'] = self._exceptions
        get_global_api().request_with_refresh_expired_access_token(path='/edr-connector/summary',
                                                                   data=summary_report,
                                                                   method='POST')
        _logger.info(summary_report)

    def send_notes(self, file_hash: str, analysis: Analysis):
        note = get_analysis_summary(analysis)
        _, alert_ids = self.running_analysis_id_and_alert_ids_by_hash[file_hash]
        self.finished_analyses_count += 1
        self.handled_alerts_count += len(alert_ids)
        self.edr_proxy.send_note(list(alert_ids), note)

        self.handled_alerts.update(list(alert_ids))
        del self.running_analysis_id_and_alert_ids_by_hash[file_hash]

    def get_file_analysis_if_recent_enough(self, file_hash: str) -> Optional[Analysis]:
        analysis = get_latest_analysis(file_hash=file_hash, private_only=True)
        if not analysis:
            return None
        try:
            analysis.get_root_analysis()
        except HTTPError:
            _logger.info(f'{analysis.analysis_id} is not a composed analysis.')
            return None

        days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=self.latest_analysis_limit_in_days)
        analysis_time = datetime.datetime.strptime(analysis.result()['analysis_time'], '%a, %d %b %Y %X GMT')
        if analysis_time < days_ago:
            return None

        return analysis

    def _analyze_alert(self, alert_info: AlertInfo) -> Optional[Analysis]:
        if self._should_skip(alert_info):
            return None

        try:
            _logger.info(f'Analyzing alert {alert_info.alert_id}')
            analysis = self.get_file_analysis_if_recent_enough(alert_info.file_hash)
            if not analysis:
                try:
                    _logger.info('analyze by hash')
                    analysis = Analysis(file_hash=alert_info.file_hash)
                    analysis.send()
                except HashDoesNotExistError:
                    _logger.info('analyze by file')
                    analysis = self.analyze_by_file(alert_info)
                    if analysis:
                        analysis.send(requester=self.edr_type.value.lower())
            return analysis

        except Exception as ex:
            self.handle_exception(ex,
                                  message='failure in analyzing file',
                                  extra_info=dict(alert_id=alert_info.alert_id, file_hash=alert_info.file_hash))

    def get_handled_alerts(self, alerts_info: List[AlertInfo]):
        handled_alerts = set()
        for alert_info in alerts_info:
            try:
                for note_info in self.edr_proxy.get_notes(alert_info.alert_id):
                    if note_info.text.startswith('Intezer Analyze'):
                        handled_alerts.add(alert_info.alert_id)
                        break
            except RuntimeError as ex:
                self.handle_exception(ex, message='error fetching notes', extra_info={'alert_id': alert_info.alert_id})

        self.handled_alerts = handled_alerts

    def analyze_alerts(self, alerts_info: List[AlertInfo]):
        analyses = set()
        for alert_info in alerts_info:
            analysis = self._analyze_alert(alert_info)
            if analysis:
                analyses.add((alert_info.file_hash, analysis))
                alert_ids = {alert_info.alert_id}
                self.running_analysis_id_and_alert_ids_by_hash[alert_info.file_hash] = (analysis.analysis_id,
                                                                                        alert_ids)

        self.wait_for_completion_with_retry(analyses)

    def wait_for_completion_with_retry(self,
                                       analyses: set,
                                       timeout_in_minutes: datetime.timedelta = datetime.timedelta(minutes=10)):
        start_time = datetime.datetime.utcnow()
        while datetime.datetime.utcnow() - start_time < timeout_in_minutes:
            if not analyses:
                break

            for file_hash, analysis in analyses.copy():
                try:
                    analysis.wait_for_completion(timeout=0)
                    _logger.info(f'analysis completed {analysis.analysis_id}')
                    self.send_notes(file_hash, analysis)
                    analyses.remove((file_hash, analysis))
                except TimeoutError:
                    continue

    def handle_alerts(self):
        while True:
            self.handled_alerts_count = 0
            self.finished_analyses_count = 0
            self._exceptions = []
            start_time = datetime.datetime.utcnow()
            try:
                alerts_info = self.edr_proxy.fetch_latest_alerts(self.latest_edr_alerts_in_hours)
                if not self.handled_alerts:
                    self.get_handled_alerts(alerts_info)
                self.analyze_alerts(alerts_info)
            except Exception as ex:
                self.handle_exception(ex)
            finally:
                self.send_summary_report()

            delta = datetime.datetime.utcnow() - start_time
            sleep_time_in_seconds = self.cooldown_between_runs_in_minutes * 60 - divmod(delta.seconds, 60)[1]
            if sleep_time_in_seconds > 0:
                _logger.info(f'No more alerts! going to sleep.')
                time.sleep(sleep_time_in_seconds)

    def handle_exception(self, ex: Exception, message: str = 'Error:', extra_info: Optional[dict] = None):
        _logger.exception(message, exc_info=True, extra=extra_info)
        self._exceptions.append(repr(ex))
