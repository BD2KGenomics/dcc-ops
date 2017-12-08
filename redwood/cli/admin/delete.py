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
from io import BytesIO

logger = logging.getLogger('admin-delete')
logger.setLevel(level=logging.INFO)
strmhd = logging.StreamHandler()
strmhd.setLevel(level=logging.INFO)
logger.addHandler(strmhd)


class ICDCDException(Exception):
    """
    Base exception class for RedwoodBucketDeleter
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
    def __init__(self, file_name=""):
        """
        Initializes error message

        Parameters
        ----------
        file_name: str
            File name of the config file with problems
        """
        self.file_name = file_name
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


class RedwoodFileNotFoundError(ICDCDException):
    """
    Should be thrown if file wasn't found
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
        self.message = "Cannot find the file with the uuid {}." \
                       " The file uuid may be incorrect or the file is not" \
                       " in the bucket.".format(self.file_uuid)


class RedwoodMissingDataError(ICDCDException):
    def __init__(self, message=""):
        """
        Initializes error message

        Parameters
        ----------
        message: str
            Error Message
        """
        self.message = message


class RedwoodFileMetadataDAO:
    """

    Attributes
    -----------
    """

    FILE_NAME_KEY = 'fileName'
    FILE_NAME_BUNDLE_ID = 'gnosId'

    def __init__(self, endpoint, mongodb_container_name=None,
                 table_url=None):
        self.mongodb_container_name = mongodb_container_name or \
                                      defaults.MONGODB_CONTAINER
        self.table_url = table_url or defaults.MONGODB_URL
        self.endpoint = endpoint

    def _run_mongo_shell_script(self, js_command):
        client = docker.APIClient()
        exec_info = client.exec_create(defaults.MONGODB_CONTAINER,
                                       ['mongo', self.table_url, '--quiet',
                                        '--eval', js_command])
        res = client.exec_start(exec_info['Id'])
        return res.strip()

    def delete_entity(self, file_uuid):
        delete_js = "var result = db.Entity.deleteMany(" \
                    "{ _id: '{file_name}'});" \
                    "printjson(result);".replace('{file_name}', file_uuid)
        res = self._run_mongo_shell_script(delete_js)

        if json.loads(res)['deletedCount'] < 1:
            raise MetadataDeleteError(file_uuid)

    def get_file_metadata(self, file_uuid, context=None):
        context = context or self._generate_fake_context()

        url = 'https://metadata.{}/entities/{}'.format(
            self.endpoint, file_uuid)
        try:
            return json.load(urllib2.urlopen(url, context=context))
        except urllib2.HTTPError as e:
            if e.code == 404:
                raise RedwoodMissingDataError(
                    "Unable to find metadata entry "
                    "at {} for File {}.".format(url, file_uuid))

    def get_bundle_metadata_info(self, bundle_id, context=None):
        context = context or self._generate_fake_context()
        url = 'https://metadata.{}/entities?fileName={}&gnosId={}'.format(
            self.endpoint, defaults.BUNDLE_METADATA_FILENAME, bundle_id)
        return json.load(urllib2.urlopen(url, context=context))

    @staticmethod
    def _generate_fake_context():
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
    Contains all the settings from a given DCC-Ops directory.

    Attributes
    -----------
    dccops_dir: str
        The root directory of the DCC-Ops repository
    _env_vars: dict
        A dictionary of all the environment variables in DCC-Ops
    """

    def __init__(self, dcc_ops_directory):
        """
        Collects the environment variables from Boardwalk,
        Action Service, and Redwood from the DCC-Ops repository.
        Also, sets the dcc ops directory.

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

        This is done by first reading each line in the file. Then, the var name
        and value extracted from the line by splitting the it using
        the "=" character as the delimiter. Afterwards the var name is
        modified by adding to the repo name to prevent conflicts with variables
        with the same name but from different repos. The final key-value pair
        should like the following example.

        Then, the dictionary entry is added to the dict, self._env_vars.

        Parameters
        ----------
        repo_subdir: str
            the repo's sub-directory containing the
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
    Deletes Files from the AWS S3 buckets used by the Redwood Storage System.
    Also, handles any information related to the file deletion.

    When deleting a file using the RedwoodBucketDeleter, the file is deleted
    and then its file_name/file_name is added to the deleted_list file.

    Attributes
    ----------
    bucket_name: str
        The name of the AWS S3 bucket with the soon-to-be-deleted files.
    data_root_folder: str
        The root folder of where all the bundle's files and metadata are saved.
    deleted_list_filename : str
        The location of the deleted_list file.
    """

    def __init__(self, dcc_ops_env):
        """
        Gets the AWS keys from the storage_settings and saves them as
        environment variables. Then, the aws keys are validated.

        Parameters
        ----------
        dcc_ops_env:

        Raises
        ------
        RedwoodDeleteInvalidConfigFile
            The config file is missing important options
        """

        os.environ['AWS_ACCESS_KEY_ID'] = dcc_ops_env.get_env_var(
            DCCOpsRepo.REDWOOD,
            defaults.DCCOPS_ENV_NAME_ACCESS_ID)

        os.environ['AWS_SECRET_ACCESS_KEY'] = dcc_ops_env.get_env_var(
            DCCOpsRepo.REDWOOD,
            defaults.DCCOPS_ENV_NAME_SECRET_KEY)
        self.bucket_name = dcc_ops_env.get_env_var(
            DCCOpsRepo.REDWOOD,
            defaults.DCCOPS_ENV_NAME_REDWOOD_BUCKET)
        self.base_endpoint = dcc_ops_env.get_env_var(
            DCCOpsRepo.REDWOOD,
            defaults.DCCOPS_ENV_NAME_REDWOOD_ENDPOINT)
        self.data_root_folder = defaults.METADATA_FILE_ROOT_FOLDER
        self.deleted_list_filename = defaults.DELETED_LIST_FILENAME
        self.env_settings = DCCOpsEnv(defaults.DCCOPS_DEFAULT_LOCATION)
        self.validate_aws_credentials()
        self.redwood_metadata_dao = RedwoodFileMetadataDAO(self.base_endpoint)

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


        Parameters
        ----------
        file_uuid: str
            The file_name of the soon-to-be deleted file

        Raises
        ------
        RedwoodDeleteFileNotFound
            the file isn't found in the bucket
        RedwoodDeleteIncompleteError
            the file still exists in the bucket after deletion
        """

        s3_client = boto3.client('s3')
        target_file_name = "{}/{}".format(self.data_root_folder, file_uuid)
        listing_info_file_name = "{}/{}.meta".format(self.data_root_folder,
                                                     file_uuid)
        logger.info("Starting Deletion for {}...".format(file_uuid))

        file_metadata = self.redwood_metadata_dao.get_file_metadata(file_uuid)
        bundle_metadata = self.redwood_metadata_dao.\
            get_bundle_metadata_info(file_metadata['gnosId'])
        bundle_metadata_json_uuid = bundle_metadata['content'][0]['id']

        logger.info("Found file metadata for {} ({}) from Bundle {}\n"
                    "Editing Bundle's metadata.json"
                    " ({})...".format(file_metadata['fileName'],
                                      file_uuid,
                                      file_metadata['gnosId'],
                                      bundle_metadata_json_uuid))

        self._add_deletion_flag_in_bundle_metadata(file_metadata['fileName'],
                                                   bundle_metadata_json_uuid)

        logger.info("Deleting entry in redwood-metadata-db...")

        self._clear_metadata_db_entry(file_uuid)

        logger.info("Deleting {} and"
                    " its meta file  ({})...".format(file_uuid,
                                                     file_metadata['fileName'])
                    )

        if not self.check_file_exists(target_file_name):
            missing_file_name = target_file_name
        elif not self.check_file_exists(listing_info_file_name):
            missing_file_name = listing_info_file_name
        else:
            missing_file_name = ''

        if missing_file_name:
            raise RedwoodFileNotFoundError(missing_file_name)
        else:
            s3_client.delete_object(Bucket=self.bucket_name,
                                    Key=target_file_name)
            s3_client.delete_object(Bucket=self.bucket_name,
                                    Key=listing_info_file_name)

        if self.check_file_exists(target_file_name):
            raise RedwoodDeleteError(file_uuid)

        logger.info("Creating file entry in redwood-metadata-db"
                    " ({})...".format(file_uuid))
        self._record_deletion_data(file_uuid)

    def _record_deletion_data(self, file_uuid):
        """

        Parameters
        ----------
        file_uuid: str
            The file_name of the deleted file
        """

        s3_client = boto3.client('s3')
        deleted_file_data = BytesIO()
        deletion_dict = {}

        if self.check_file_exists(self.deleted_list_filename):
            s3_client.download_fileobj(self.bucket_name,
                                       self.deleted_list_filename,
                                       deleted_file_data)
            try:
                deletion_dict = json.loads(deleted_file_data.getvalue())
            except ValueError:
                logger.warn("Deletion History Log "
                            "format's is incorrect.")

        deletion_dict.setdefault('deletedFiles', [])
        if file_uuid not in deletion_dict['deletedFiles']:
            deletion_dict['deletedFiles'].append({"file_name": file_uuid})
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
        try:
            self.redwood_metadata_dao.delete_entity(file_uuid)
        except MetadataDeleteError:
            logger.error('Unable to delete metadata'
                         ' server entry for file {}'.format(file_uuid))

    def _add_deletion_flag_in_bundle_metadata(self, file_name,
                                              metadata_file_uuid):
        file_location = "{}/{}".format(self.data_root_folder,
                                       metadata_file_uuid)
        s3_client = boto3.client('s3')
        if self.check_file_exists(file_location):
            old_metadata_file = BytesIO()
            s3_client.download_fileobj(self.bucket_name, file_location,
                                       old_metadata_file)
            old_metadata = json.loads(old_metadata_file.getvalue())

            for wo in old_metadata["specimen"][0]["samples"][0]\
                    ["analysis"][0]["workflow_outputs"]:
                if file_name == wo['file_path']:
                    wo['is_deleted'] = True

            new_metadata = str(json.dumps(old_metadata)).decode()
            s3_client.put_object(Body=new_metadata,
                                 Bucket=self.bucket_name,
                                 Key=file_location)
        else:
            raise RedwoodFileNotFoundError(metadata_file_uuid)


def run_delete_file_cli(deleter, file_uuid, will_force):
    """
    The command interface for deleting a file in AWS S3 Buckets

    Parameters
    ----------
    deleter: RedwoodBucketDAO
        The object that manages file deletion
    file_uuid
        The file_name of the file targeted for deletion
    will_force
        If this value is True, then the user will not be asked to confirm
        the deletion
    """

    resp = ""

    if not will_force:
        resp = raw_input("Are you sure you want to delete {}?"
                         " [Y]es/[N]o ".format(file_uuid))

    if resp.lower() in {'y', 'yes'} or will_force:
        try:
            deleter.delete_file(file_uuid)
        except RedwoodDeleteError as e:
            print str(e)
        except RedwoodFileNotFoundError as e:
            print str(e)
        else:
            print "Successfully deleted File {}.".format(file_uuid)
    else:
        print "DID NOT delete File {}.".format(file_uuid)


def run_cli():
    """
    Initiates the command line interface for admin delete.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument('-f', "--force",
                        help='Skips Confirmation Prompt.',
                        action="store_true")
    parser.add_argument('FILE_UUID',
                        help='The file uuid of the file that will be'
                             ' deleted.')
    args = parser.parse_args()

    dccops_env_vars = DCCOpsEnv(defaults.DCCOPS_DEFAULT_LOCATION)

    if os.getuid() == 0:
        try:
            deleter = RedwoodAdminDeleter(dccops_env_vars)
        except ICDCDBadAWSKeys as e:
            print str(e)
            print "Please check if your AWS keys are correct."
        else:
            run_delete_file_cli(deleter, args.FILE_UUID, args.force)
    else:
        print "Please run this script as root."


if __name__ == '__main__':
    run_cli()
