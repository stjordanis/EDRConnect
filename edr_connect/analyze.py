import argparse
import os

from edr_connect.utils.utils import create_config_from_file
from managers.analysis_manager import AnalysisManager
from managers.analysis_manager import EDRType

if __name__ == '__main__':
    config = create_config_from_file('./config/config.yaml')
    if not config.get('config_enabled'):
        parser = argparse.ArgumentParser(description='Analyze argument parse')
        parser.add_argument('--edr-api-key', default=os.environ.get('EDR_API_KEY'))
        parser.add_argument('--intezer-api-key', default=os.environ.get('INTEZER_API_KEY'))
        parser.add_argument('--type', choices=['S1'], default=os.environ.get('EDR_TYPE'))
        parser.add_argument('--base-address', default=os.environ.get('EDR_BASE_ADDRESS'))
        parser.add_argument('--ssl-verification', default=os.environ.get('EDR_SSL_VERIFICATION', False), action="store_true")
        parser.add_argument('--latest-edr-alerts', type=int,
                            default=os.environ.get('LATEST_EDR_ALERTS_LIMIT_IN_HOURS', 72))
        parser.add_argument('--latest-analysis-limit', type=int,
                            default=os.environ.get('LATEST_ANALYSIS_LIMIT_IN_DAYS', 30))
        parser.add_argument('--cooldown', type=int, default=os.environ.get('COOLDOWN_BETWEEN_RUNS_IN_MINUTES', 15))
        parser.add_argument('--http-timeout', type=int, default=os.environ.get('HTTP_TIMEOUT_IN_SECONDS', 60))
        parser.add_argument('--download-retries', type=int, default=os.environ.get('FILE_DOWNLOAD_NUM_OF_RETRIES', 3))
        parser.add_argument('--download-timeout', type=int, default=os.environ.get('FILE_DOWNLOAD_TIMEOUT_IN_SECONDS', 10))
        args = parser.parse_args()

        edr_api_key = args.edr_api_key
        intezer_api_key = args.intezer_api_key
        base_address = args.base_address
        edr_type = EDRType(args.type)
        ssl_verification = args.ssl_verification
        latest_analysis_limit = args.latest_analysis_limit
        latest_edr_alerts = args.latest_edr_alerts
        cooldown = args.cooldown
        http_timeout = args.http_timeout
        download_retries = args.download_retries
        download_timeout = args.download_timeout
    else:
        edr_api_key = config.get('edr_api_key')
        intezer_api_key = config.get('intezer_api_key')
        base_address = config.get('base_address')
        edr_type = EDRType(config.get('type'))
        ssl_verification = config.get('ssl_verification', False)
        latest_edr_alerts = config.get('latest_edr_alerts_limit_in_hours', 72)
        latest_analysis_limit = config.get('latest_analysis_limit_in_days', 30)
        cooldown = config.get('cooldown_in_minutes', 15)
        http_timeout = config.get('http_timeout_in_seconds', 60)
        download_retries = config.get('download_retries', 3)
        download_timeout = config.get('download_timeout_in_seconds', 10)

    analysis_manager = AnalysisManager(edr_api_key,
                                       intezer_api_key,
                                       base_address,
                                       edr_type,
                                       ssl_verification,
                                       latest_analysis_limit,
                                       latest_edr_alerts,
                                       cooldown,
                                       http_timeout,
                                       download_retries,
                                       download_timeout)

    analysis_manager.handle_alerts()
