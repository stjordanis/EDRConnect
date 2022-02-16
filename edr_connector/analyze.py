import argparse
import os

from managers.analysis_manager import AnalysisManager
from managers.analysis_manager import EDRType

if __name__ == '__main__':
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
    parser.add_argument('--http-timeout', type=int, default=os.environ.get('DEFAULT_HTTP_TIMEOUT_IN_SECONDS', 60))
    parser.add_argument('--download-retries', type=int, default=os.environ.get('FILE_DOWNLOAD_NUM_OF_RETRIES', 3))
    parser.add_argument('--download-timeout', type=int, default=os.environ.get('FILE_DOWNLOAD_TIMEOUT_IN_SECONDS', 10))

    args = parser.parse_args()

    analysis_manager = AnalysisManager(args.edr_api_key,
                                       args.intezer_api_key,
                                       args.base_address,
                                       EDRType(args.type),
                                       args.ssl_verification,
                                       args.latest_analysis_limit,
                                       args.latest_edr_alerts,
                                       args.cooldown,
                                       args.http_timeout,
                                       args.download_retries,
                                       args.download_timeout)
    analysis_manager.handle_alerts()
