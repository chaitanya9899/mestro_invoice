import os
import time

DEBUG = True
API_URL_PREFIX = "/mestro/crawler"
HOST = '0.0.0.0'
PORT = 5001

ENABLE_CORS = False

# Supported agent configuration file
APPLICATION_STATIC_PATH = ''
AGENT_CONFIG_FILEPATH   = 'agent_configs/agents.json'

AGENT_CONFIG_PKL_FILEPATH = 'agent_configs/agents.pkl'

# Application configuration
BASIC_HTTP_USERAME = os.environ.get('BASIC_HTTP_USERAME')
BASIC_HTTP_PASSWORD = os.environ.get('BASIC_HTTP_PASSWORD')

ELASTIC_DB_URL = os.environ.get('ELASTIC_DB_URL')


ES_LOG_INDEX = 'mestro-app-logs-v2'
ES_JOB_INDEX = 'mestro-job-stats-v4'
ES_DATA_INDEX = 'mestro-scraped-data'
ES_DATA_INDEX_2 = 'mestro-crawled-data-v2'

JOB_RUNNING_STATUS = 'RUNNING'
JOB_COMPLETED_SUCCESS_STATUS = 'COMPLETED_SUCCESS'
JOB_COMPLETED_FAILED_STATUS = 'COMPLETED_FAILED'