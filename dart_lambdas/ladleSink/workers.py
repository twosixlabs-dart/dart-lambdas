import json
import boto3
import botocore
import os
import hashlib
import urllib.parse
from dart_lambdas.common.retry import retry

from dart_lambdas.common.http_utils import try_post


def get_created_object(record_in, bucket_in):
    key = urllib.parse.unquote_plus(record_in['s3']['object']['key'])
    s3_client = boto3.client('s3')

    try:
        get_response = retry(s3_client.get_object, {'Bucket': bucket_in, 'Key': key}, 300, None, 100)
    except Exception as e:
        return False, key, None, f'Exception: {str(e)}'  # Deliver what we can, send exception message

    raw_doc_out = get_response['Body'].read()
    return True, key, raw_doc_out, None

def get_created_object_metadata(record_in, bucket_in):
    key = urllib.parse.unquote_plus(record_in['s3']['object']['key'])
    key_metadata = ".".join( key.split('.')[0:-2] ) + '.meta'
    s3_client = boto3.client('s3')

    try:
        get_response = retry(s3_client.get_object, {'Bucket': bucket_in, 'Key': key_metadata}, 300, None, 100)
    except Exception as e:
        return False, key_metadata, None, f'Exception: {str(e)}'  # Deliver what we can, send exception message

    metadata_out = get_response['Body'].read().decode('utf-8')
    return True, key_metadata, metadata_out, None


def post_retrieved_object_and_metadata(key_in, raw_doc_in, metadata_in):
    DART_URL = os.environ.get('DART_URL')
    SUBMISSION_PORT = os.environ.get('SUBMISSION_PORT')
    SUBMISSION_ENDPOINT = os.environ.get('SUBMISSION_ENDPOINT')
    FACTIVA_SUBMISSION_ENDPOINT = os.environ.get('FACTIVA_SUBMISSION_ENDPOINT')
    BAUTH_PASSWORD = os.environ.get('BAUTH_PASSWORD')
    BAUTH_USERNAME = os.environ.get('BAUTH_USERNAME')

    is_not_factiva = False if key_in.split('.')[-1] == 'factiva' else True

    file_dict = \
        {
            'file': (key_in, raw_doc_in),
        } if metadata_in is None else {
            'file': (key_in, raw_doc_in),
            'metadata': (None, metadata_in, 'application/json'),
        }

    return try_post(
            url=DART_URL,
            port=SUBMISSION_PORT,
            endpoint=SUBMISSION_ENDPOINT if is_not_factiva else FACTIVA_SUBMISSION_ENDPOINT,
            basic_auth=(BAUTH_USERNAME, BAUTH_PASSWORD),
            post_files=file_dict,
            post_data=None,
            sleep_time=0,
            numtimes=1
        )


def get_key_from_ladle_doc_id(json_in, old_key):
    parsed_json = json.loads(json_in)
    suffix = old_key.split('.')[-2].lower()
    return f'{parsed_json["document_id"]}.{suffix}'


def move_processed_object(input_key, input_bucket, output_key, output_bucket):
    s3_client = boto3.client('s3')

    try:
        s3_client.copy_object(
            Bucket=output_bucket,
            Key=output_key,
            CopySource={
                "Bucket": input_bucket,
                "Key": input_key,
            }
        )
    except botocore.exceptions.ClientError as e:
        return False, f"Unable to copy {input_key} from {input_bucket} to {output_key} in {output_bucket}: {str(e)}"

    try:
        s3_client.delete_object(Bucket=input_bucket, Key=input_key)
    except botocore.exceptions.ClientError as e:
        try:
            s3_client.delete_object(Bucket=output_bucket, Key=output_key)
            return False, f"Unable to remove {input_key} from {input_bucket}. Undid copy to {output_bucket}.\n\nException {str(e)}"
        except botocore.exceptions.ClientError as e2:
            return False, f"Unable to remove {input_key} from {input_bucket}. Unable to undo copy to {output_bucket}.\n\nRemoval of original Exception: {str(e)}\n\nRemoval of copy Exception: {str(e2)}"

    return True, f"Successfully moved {input_key} from {input_bucket} to {output_key} in {output_bucket}"
