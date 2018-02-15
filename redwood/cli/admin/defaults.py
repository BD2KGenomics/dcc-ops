"""
    The default constants of used by admin scripts.
"""

import os


def get_parent_directory(url, level=1):
    return "/".join(url.split('/')[:-level])


DCCOPS_DEFAULT_LOCATION = get_parent_directory(os.path.abspath(__file__),
                                               level=4)
DCCOPS_ENV_NAME_ACCESS_ID = 'access_key'
DCCOPS_ENV_NAME_SECRET_KEY = 'secret_key'
DCCOPS_ENV_NAME_REDWOOD_ENDPOINT = 'base_url'
DCCOPS_ENV_NAME_REDWOOD_BUCKET = 's3_bucket'
DCCOPS_ENV_FILENAME = '.env'
DCCOPS_BOARDWALK_SUB_DIR = 'boardwalk'
DCCOPS_ACTION_SERVICE_SUB_DIR = 'action'
DCCOPS_REDWOOD_SUB_DIR = 'redwood'

METADATA_FILE_ROOT_FOLDER = 'data'

DELETED_LIST_FILENAME = 'deleted_file_list'

MONGODB_CONTAINER = 'redwood-metadata-db'
DEFAULT_MONGODB_HOST = '127.0.0.1:27017'
DEFAULT_MONGODB_DB_NAME = 'dcc-metadata'
MONGODB_URL = "{}/{}".format(DEFAULT_MONGODB_HOST,
                             DEFAULT_MONGODB_DB_NAME)

INDEXER_CONTAINER = 'boardwalk_dcc-metadata-indexer_1'

BUNDLE_METADATA_FILENAME = 'metadata.json'
