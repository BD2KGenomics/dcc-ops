"""
delete.py

This script allows developers to delete files generated from  redwood storage
system.
"""

import argparse
import os
import json
import boto3
import botocore
import defaults
import docker
import logging
import urllib2
import ssl
import datetime
from io import BytesIO

logger = logging.getLogger('admin-delete')
logger.setLevel(level=logging.INFO)
strmhd = logging.StreamHandler()
strmhd.setLevel(level=logging.INFO)
logger.addHandler(strmhd)


class ICDCDException(Exception):
    """
    Base exception class for DCCOPS admin scripts
    """

    message = None

    def __repr__(self):
        """
        Should have the same functionality as self.__str__()

        Returns
        -------
        str
            output of self.__str__()
        """
        return self.__str__()

    def __str__(self):
        """
        Outputs a formatted error message

        Returns
        -------
        str
            A formatted error message
        """
        return "{}: {}".format(self.__class__.__name__, self.message)


class MetadataDeleteError(ICDCDException):
    """
    Thrown if a file metadata entry couldn't be deleted
    """
    def __init__(self, file_uuid=""):
        """
        Initializes error message

        Parameters
        ----------
        file_uuid: str
            file_uuid of the file metadata
        """
        self.file_name = file_uuid
        self.message = "Unable to remove file " \
                       " {} from Metadata Server".format(self.file_name)


class ICDCDBadAWSKeys(ICDCDException):
    """
    Should be thrown the AWS given are not valid for accessing S3 buckets
    """
    def __init__(self):
        """
        Initializes error message
        """

        self.message = "AWS didn't receive the right access" \
                       " and secret access keys."


class RedwoodDeleteError(ICDCDException):
    """
    Should be thrown if file wasn't deleted properly
    """
    def __init__(self, file_name=""):
        """
        Initializes error message

        Parameters
        ----------
        file_name: str
            File uuid of the file that can't be deleted
        """
        self.file_name = file_name
        self.message = "Unable to delete File {}." \
                       " File still exists in bucket".format(self.file_name)


class ForbiddenDeleteError(ICDCDException):
    """
    Thrown if a file that shouldn't be deleted was about to be deleted.
    """
    def __init__(self, message=""):
        """
        Initializes error message

        Parameters
        ----------
        message: str
            Error Message
        """
        self.message = message


class RedwoodFileNotFoundError(ICDCDException):
    """
    Should be thrown if a file wasn't found
    """
    def __init__(self, file_uuid=""):
        """
        Initializes error message

        Parameters
        ----------
        file_uuid: str
            File UUID that can't be found
        """
        self.file_uuid = file_uuid
        self.message = "Cannot find the file named {}." \
                       " The file uuid may be incorrect or the file is not" \
                       " in the bucket.".format(self.file_uuid)


class RedwoodMissingDataError(ICDCDException):
    """
    Thrown if specific metadata wasn't in the file metadata database
    """
    def __init__(self, message=""):
        """
        Initializes error message

        Parameters
        ----------
        message: str
            Error Message
        """
        self.message = message


class RedwoodFileMetadataAPI:
    """
    Retrieves and modifies data from the redwood metadata server by
    accessing the https website or the MongoDB container directly

    Attributes
    -----------
    endpoint : str
        The base url of the https metadata website
    mongodb_container_name : str
        The name of the docker container where the metadata
        database is located
    table_url : str
        The exposed url of the MongoDB dcc-metadata database
    """

    FILE_NAME_KEY = 'fileName'
    FILE_NAME_BUNDLE_ID = 'gnosId'

    def __init__(self, endpoint, mongodb_container_name=None,
                 table_url=None):
        """
        Initializes attributes

        Parameters
        ----------
        endpoint : str
            The base url of the https metadata website
        mongodb_container_name : str
            The name of the docker container where the metadata
            database is located
        table_url : str
            The exposed url of the mongoDB dcc-metadata database
        """
        self.mongodb_container_name = mongodb_container_name or \
                                      defaults.MONGODB_CONTAINER
        self.table_url = table_url or defaults.MONGODB_URL
        self.endpoint = endpoint

    def _run_mongo_shell_script(self, js_command):
        """
        Access the redwood-metadata-db docker container. Then, runs a MongoDB
        shell command by using the given javascript command

        Parameters
        ----------
        js_command
            The javascript command that the MongoDB shell will execute

        Returns
        -------
        str
            The output from MongoDB shell script
        """

        client = docker.APIClient()
        exec_info = client.exec_create(defaults.MONGODB_CONTAINER,
                                       ['mongo', self.table_url, '--quiet',
                                        '--eval', js_command])
        res = client.exec_start(exec_info['Id'])
        return res.strip()

    def delete_entity(self, file_uuid):
        """
        Deletes the file metadata from the file metadata server by executing
        a MongoDB shell delete command in the metadata server's docker
        container.

        Parameters
        ----------
        file_uuid : str
            The file_uuid of the target deleted file to locate the database
            entry

        Raises
        -------
        MetadataDeleteError
            Either the file metadata database is unable to delete the file's
            entry or the database doesn't contain any entries with the given
            file_uuid
        """

        delete_js = "var result = db.Entity.deleteMany(" \
                    "{ _id: '{file_name}'});" \
                    "printjson(result);".replace('{file_name}', file_uuid)
        res = self._run_mongo_shell_script(delete_js)

        if json.loads(res)['deletedCount'] < 1:
            raise MetadataDeleteError(file_uuid)

    def get_file_metadata(self, file_uuid, context=None):
        """
        Gets the file metadata from the https metadata website

        Parameters
        ----------
        file_uuid : str
            The target file's uuid for locating its file metadata
        context : ssl.SSLContext, optional
            The custom context for accessing the metadata website. Will default
            to a context with a fake cert.

        Returns
        -------
        dict
            the file metadata of the target file

        Raises
        ------
        RedwoodMissingDataError
            Can't find the file metadata with the given file_uuid
        """

        context = context or self._generate_fake_context()

        url = 'https://metadata.{}/entities/{}'.format(
            self.endpoint, file_uuid)
        try:
            return json.load(urllib2.urlopen(url, context=context))
        except urllib2.HTTPError as e:
            if e.code == 404:
                error_msg = "Unable to find metadata entry " \
                            "at {} for File {}.".format(url, file_uuid)
                raise RedwoodMissingDataError(error_msg)
            else:
                raise

    def get_bundle_metadata_info(self, bundle_id, context=None):
        """
        Gets the file metadata of the
        bundle's metadata.json (bundle metadata file) from the https metadata
        website

        Parameters
        ----------
        bundle_id : str
            The metadata.json's bundle uuid
        context : ssl.SSLContext, optional
            The context for accessing the metadata website

        Returns
        --------
        dict
            The file metadata of the target bundle's
            metadata.json (bundle metadata file)
        """

        context = context or self._generate_fake_context()
        url = 'https://metadata.{}/entities?fileName={}&gnosId={}'.format(
            self.endpoint, defaults.BUNDLE_METADATA_FILENAME, bundle_id)
        return json.load(urllib2.urlopen(url, context=context))

    @staticmethod
    def _generate_fake_context():
        """
        Generates a fake ssl.SSLContext for retrieving json data by https

        Returns
        -------
            An ssl.SSLContext containing a fake cert
        """
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx


class DCCOpsRepo:
    """
    An enumeration representing the repositories used by DCC-Ops
    """

    BOARDWALK = 'boardwalk'
    ACTION_SERVICE = 'action_service'
    REDWOOD = 'redwood'


class DCCOpsEnv:
    """
    Contains all the settings from DCC-Ops.

    Attributes
    -----------
    dccops_dir: str
        The root directory of the DCC-Ops repository
    _env_vars: dict
        A dictionary of all repos in DCC-Ops. Each repo contains a list
        the environment variables used by that repo
    """

    def __init__(self, dcc_ops_directory):
        """
        Collects the environment variables from Boardwalk,
        Action Service, and Redwood from the DCC-Ops repository.
        Also, initializes the dcc ops directory attribute.

        Parameters
        ----------
        dcc_ops_directory: str
            The directory of the DCC-Ops directory
        """

        self.dccops_dir = dcc_ops_directory
        self._env_vars = {}
        self._sync_settings(DCCOpsRepo.BOARDWALK,
                            defaults.DCCOPS_BOARDWALK_SUB_DIR)
        self._sync_settings(DCCOpsRepo.ACTION_SERVICE,
                            defaults.DCCOPS_ACTION_SERVICE_SUB_DIR)
        self._sync_settings(DCCOpsRepo.REDWOOD,
                            defaults.DCCOPS_REDWOOD_SUB_DIR)

    def _sync_settings(self, repo, repo_subdir,
                       env_vars_filename=defaults.DCCOPS_ENV_FILENAME):
        """
        Gathers the environment variables from the environment variable file
        of a the given module sub-directory in DCC-Ops.

        This is done by first reading each line in the file environment
        variable file. Then, the var name and value extracted from the line by
        splitting the it using the "=" character as the delimiter. Then, the
        variable name and value are saved in a dictionary.

        Parameters
        ----------
        repo_subdir: str
            the repo's sub-directory containing the environment variable file
        env_vars_filename: str, optional
            the filename of the environment variable file
        repo: DCCOpsRepo, str
            The repo where the environment variable is located
        """

        with open(os.path.join(self.dccops_dir, repo_subdir,
                               env_vars_filename), 'r') as env_file:
            var_dict = {}
            for setting in env_file.readlines():
                if '=' in setting:
                    var_name, var_setting = setting.split('=')
                    var_dict[var_name] = var_setting.strip()
            self._env_vars[repo] = var_dict

    def get_env_var(self, repo, var_name):
        """
        Gets the value of the environment variable from the given repo and var
        name

        Parameters
        ----------
        repo: DCCOpsRepo, str
            The repo where the environment variable is located
        var_name: str
            The name of the environment variable

        Returns
        -------
        str
            The value of the environment variable from the given repo and var
            name
        """
        return self._env_vars[repo][var_name]


class RedwoodAdminDeleter:
    """
    Deletes files from the AWS S3 buckets used by the Redwood Storage System.
    Also, handles any information related to the file deletion.

    Attributes
    ----------
    bucket_name : str
        The name of the AWS S3 bucket containing the files selected for
        deletion.
    base_endpoint : str
        the base url for the redwood metadata server
    data_root_folder : str
        The root folder of where all the bundle's files and metadata are saved.
    deleted_list_filename : str
        The location of the deleted_list file.
    redwood_metadata_api : RedwoodFileMetadataAPI
        For accessing and editing the file metadata in the redwood metadata
        server.
    ignore_errors : boolean
        If True, prevents errors (except ForbiddenDeleteError and
        RedwoodFileNotFoundError for the target deleted file) from
        interrupting the deletion process
    """

    def __init__(self, dcc_ops_env=None, ignore_errors=False):
        """
        Gets the all of the .env variables in DCC-Ops.
        Then, checks if the aws keys from the .env are valid. Afterwards, it
        initializes the Redwood File Metadata API, and other attributes

        Parameters
        ----------
        dcc_ops_env :

        Raises
        ------
        RedwoodDeleteInvalidConfigFile
            The config file is missing important options
        """

        self.env_settings = dcc_ops_env
        os.environ['AWS_ACCESS_KEY_ID'] = self.env_settings.get_env_var(
            DCCOpsRepo.REDWOOD,
            defaults.DCCOPS_ENV_NAME_ACCESS_ID)
        os.environ['AWS_SECRET_ACCESS_KEY'] = self.env_settings.get_env_var(
            DCCOpsRepo.REDWOOD,
            defaults.DCCOPS_ENV_NAME_SECRET_KEY)
        self.bucket_name = self.env_settings.get_env_var(
            DCCOpsRepo.REDWOOD,
            defaults.DCCOPS_ENV_NAME_REDWOOD_BUCKET)
        self.base_endpoint = self.env_settings.get_env_var(
            DCCOpsRepo.REDWOOD,
            defaults.DCCOPS_ENV_NAME_REDWOOD_ENDPOINT)
        self.data_root_folder = defaults.METADATA_FILE_ROOT_FOLDER
        self.deleted_list_filename = defaults.DELETED_LIST_FILENAME
        self.validate_aws_credentials()
        self.redwood_metadata_api = RedwoodFileMetadataAPI(self.base_endpoint)
        self.ignore_errors = ignore_errors

    @staticmethod
    def validate_aws_credentials():
        """
        Checks if the AWS access key and AWS secret access key is valid.

        Uses the list_bucket method to check the aws keys' validity. If they
        aren't valid, InvalidAccessKeyId.ClientError is caught and
        RedwoodDBadAWSKeyError is thrown instead.

        Raises
        -------
        RedwoodDBadAWSKeys
            If aws access keys are invalid
        """
        s3_client = boto3.client('s3')
        try:
            s3_client.list_buckets()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidAccessKeyId':
                raise ICDCDBadAWSKeys
            else:
                raise

    def check_file_exists(self, file_name):
        """
        Checks if there's a file with the given filename in that bucket.

        Parameters
        ----------
        file_name
            the file's name that going to be checked

        Returns
        -------
            returns True if a file with the given filename exists
            in the bucket otherwise this method returns False
        """
        s3_client = boto3.client('s3')
        try:
            s3_client.head_object(Bucket=self.bucket_name, Key=file_name)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                raise
        else:
            return True

    def delete_file(self, file_uuid):
        """
        Removes the deleted files entry in the metadata database,
        Adds a deletion flag in the file's entry in the bundle metadata.
        Removes the file's the storage listing in the redwood storage bucket.
        Finally, it deletes the file in the redwood storage system.
        If the deletion was successful, any information about the deletion is
        recorded in the deletion_file_list file in the root folder of the
        redwood storage bucket.

        Parameters
        ----------
        file_uuid: str
            The file_name of the deleted file

        Raises
        ------
        RedwoodMissingDataError
            (If ignore_errors is disabled)
            The deleted file has no file metadata in in the
            redwood metadata database
        ForbiddenDeleteError
            The deleted file contains the bundle metadata
        RedwoodFileNotFoundError
            (If ignore_errors is disabled)
            The bundle data doesn't exist in the redwood storage bucket
        """

        logger.info("Starting Deletion for {}...".format(file_uuid))

        file_metadata = {}

        try:
            file_metadata = self.redwood_metadata_api.get_file_metadata(file_uuid)
        except RedwoodMissingDataError as e:
            if self.ignore_errors:
                logging.warn(str(e))
                logging.warn("Metadata doesn't exist for this file."
                             " Skipping metadata related steps.")
            else:
                raise

        if file_metadata:
            metadata_filename = defaults.BUNDLE_METADATA_FILENAME
            bundle_id = file_metadata['gnosId']
            bundle_metadata = self.redwood_metadata_api. \
                get_bundle_metadata_info(bundle_id)

            if file_metadata['fileName'] == metadata_filename:
                raise ForbiddenDeleteError("{} is a bundle metadata file ({})"
                                           " and cannot be"
                                           " deleted".format(bundle_id,
                                                             metadata_filename)
                                           )
            bundle_metadata_json_uuid = bundle_metadata['content'][0]['id']

            logger.info("Found file metadata for {} ({}) from Bundle {}\n"
                        "Editing Bundle's metadata.json"
                        " ({})...".format(file_metadata['fileName'],
                                          file_uuid,
                                          file_metadata['gnosId'],
                                          bundle_metadata_json_uuid))

            try:
                self._add_deletion_flag_in_bundle_metadata(
                    file_metadata['fileName'],
                    bundle_metadata_json_uuid)
            except RedwoodFileNotFoundError:
                if self.ignore_errors:
                    logging.warn("This bundle ({}) no longer has its metadata"
                                 " in the bucket. Please delete the other"
                                 " files from this"
                                 " bundle".format(file_metadata['gnosId']))
                else:
                    raise
                pass

            logger.info("Deleting entry in redwood-metadata-db...")

            self._clear_metadata_db_entry(file_uuid)

        logger.info("Deleting {} ({}) and"
                    " its endpoint"
                    " listing file...".format(file_metadata.get('fileName',
                                                                '[No Metadata'
                                                                ' Found]'),
                                              file_uuid))

        target_file_name = "{}/{}".format(self.data_root_folder, file_uuid)
        listing_info_file_name = "{}/{}.meta".format(self.data_root_folder,
                                                     file_uuid)

        self._safely_delete_file(target_file_name, always_throw_error=True)
        self._safely_delete_file(listing_info_file_name)
        logger.info("Creating file entry in redwood-metadata-db"
                    " ({})...".format(file_uuid))
        self._record_deletion_data(
            file_uuid,
            file_metadata.get('fileName', '[No Metadata Found]'),
            file_metadata.get('gnosId', '[No Metadata Found]'))

    def _safely_delete_file(self, file_name, always_throw_error=False):
        """
        Deletes the file if the file exists in the bucket.

        Parameters
        ----------
        file_name: str
            The deleted file's file name

        Raises
        ------
        RedwoodFileNotFoundError
            File is not in the redwood storage S3 bucket.
        """
        s3_client = boto3.client('s3')
        if self.check_file_exists(file_name):
            s3_client.delete_object(Bucket=self.bucket_name,
                                    Key=file_name)
        elif self.ignore_errors and not always_throw_error:
            logger.warn("Unable to delete {}".format(file_name))
        else:
            raise RedwoodFileNotFoundError(file_name)

    def _record_deletion_data(self, file_uuid, file_name, bundle_uuid):
        """
        Logs info about the file deletion in a file. The name of the  file is
        the value of defaults.DELETED_LIST_FILENAME.

        The following info is recorded:
            -Deleted file's uuid
            -Deleted file's name
            -Date and time of Deletion

        Parameters
        ----------
        file_uuid: str
            The file_name of the deleted file
        """

        s3_client = boto3.client('s3')
        deleted_file_data = BytesIO()
        deletion_dict = {'deletedFiles': {'bundles': {}}}
        if self.check_file_exists(self.deleted_list_filename):
            s3_client.download_fileobj(self.bucket_name,
                                       self.deleted_list_filename,
                                       deleted_file_data)
            try:
                deletion_dict = json.loads(deleted_file_data.getvalue())
            except ValueError:
                logger.warn("Deletion History Log "
                            "format's is incorrect.")
        bundle_list = deletion_dict['deletedFiles']['bundles']
        date = datetime.datetime.now().strftime('%m-%d-%y %I:%m:%S %p')
        bundle_list.setdefault(bundle_uuid, []) \
            .append({'file_uuid': file_uuid,
                     'file_name': file_name,
                     'date_deleted': date})
        deletion_list_bytes = json.dumps(deletion_dict).encode()
        if self.check_file_exists(self.deleted_list_filename):
            s3_client.put_object(Bucket=self.bucket_name,
                                 Key=self.deleted_list_filename,
                                 Body=deletion_list_bytes)
        else:
            del_byte_io = BytesIO(deletion_list_bytes)
            s3_client.upload_fileobj(del_byte_io,
                                     self.bucket_name,
                                     self.deleted_list_filename)

    def _clear_metadata_db_entry(self, file_uuid):
        """
        Removes the deleted files entry in a mongo database in the
        redwood-metadata-db container

        Parameters
        ----------
        file_uuid
            The deleted file's file uuid

        Raises
        -------
        MetadataDeleteError
            Unable able to delete the deleted file's entry
            (if ignore_errors is disabled)
        """
        try:
            self.redwood_metadata_api.delete_entity(file_uuid)
        except MetadataDeleteError as e:
            if self.ignore_errors:
                logger.warn(str(e))
                logger.warn('Unable to delete metadata'
                            ' server entry for file {}'.format(file_uuid))
            else:
                raise

    def _add_deletion_flag_in_bundle_metadata(self, file_name,
                                              metadata_file_uuid):
        """
        This method gets the bundle's metadata.json file in the redwood storage
        S3 bucket. Then, in the json file, it finds the deleted file's entry
        under "workflow_outputs" key. Afterwards, it adds the is_deleted
        flag in the entry. It should look like the following example...

        Example
        -------
            {
                ...
                "workflow_outputs": {
                    "is_deleted": false
                    "file_type": "fake",
                    "file_sha": "fac54a",
                    "file_path": "fake_file.fakse",
                    "file_size": 8888
                }
            }

        Finally, the new metadata.json is uploaded to the S3 bucket and the old
        metadata is overwritten.

        Parameters
        ----------
        file_name: str
            the name of the deleted file
        metadata_file_uuid
            the file_uuid metadata.json of the deleted file's bundle

        Raises
        -------
        RedwoodFileNotFoundError
            The metadata.json is not in the S3 Bucket redwood storage
        """

        file_location = "{}/{}".format(self.data_root_folder,
                                       metadata_file_uuid)
        s3_client = boto3.client('s3')
        if self.check_file_exists(file_location):
            old_metadata_file = BytesIO()
            s3_client.download_fileobj(self.bucket_name, file_location,
                                       old_metadata_file)
            old_metadata = json.loads(old_metadata_file.getvalue())

            for wo in old_metadata["specimen"][0]["samples"][0] \
                    ["analysis"][0]["workflow_outputs"]:
                if file_name == wo['file_path']:
                    wo['is_deleted'] = True

            new_metadata = str(json.dumps(old_metadata)).decode()
            s3_client.put_object(Body=new_metadata,
                                 Bucket=self.bucket_name,
                                 Key=file_location)
        else:
            raise RedwoodFileNotFoundError(metadata_file_uuid)


def run_delete_file_cli(deleter, file_uuid, skip_prompt):
    """
    The command interface for deleting a file in AWS S3 Buckets

    Parameters
    ----------
    deleter: RedwoodAdminDeleter
        The object that manages file deletion
    file_uuid
        The file_name of the file targeted for deletion
    skip_prompt
        If this value is True, then the user will not be asked to confirm
        the deletion
    """

    resp = ""

    if not skip_prompt:
        resp = raw_input("Are you sure you want to delete {}?"
                         " [Y]es/[N]o ".format(file_uuid))

    if resp.lower() in {'y', 'yes'} or skip_prompt:
        try:
            deleter.delete_file(file_uuid)
        except (RedwoodDeleteError, RedwoodFileNotFoundError) as e:
            logger.error(str(e))
            logger.error("Deletion Failed")
        else:
            logger.info("Successfully deleted File {}.".format(file_uuid))
    else:
        logger.info("DID NOT delete File {}.".format(file_uuid))


def run_cli():
    """
    Initiates the command line interface for admin delete.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument('-s', "--skip-prompt",
                        help='Skips Confirmation Prompt.',
                        action="store_true")
    parser.add_argument("--ignore-errors",
                        help='Prevents most errors from interrupting the'
                             'deletion process',
                        action="store_true")
    parser.add_argument('FILE_UUID',
                        help='The file uuid of the file that will be'
                             ' deleted.')
    args = parser.parse_args()

    dccops_env_vars = DCCOpsEnv(defaults.DCCOPS_DEFAULT_LOCATION)

    if os.getuid() == 0:
        try:
            deleter = RedwoodAdminDeleter(dccops_env_vars,
                                          ignore_errors=args.ignore_errors)
        except ICDCDBadAWSKeys as e:
            logger.error(str(e))
            logger.error("Please check if your AWS keys are correct.")
        else:
            run_delete_file_cli(deleter, args.FILE_UUID, args.skip_prompt)
    else:
        logger.error("Please run this script as root.")


if __name__ == '__main__':
    run_cli()
