import mock
import botocore
import pytest
import os

from dart_lambdas.ladleSink import workers
from .test_ladle_sink import s3_object_created_event


def test_get_created_object_returns_an_object_when_it_exists(normal_env, s3_resource, s3_client):
    S3_BUCKET_IN = os.environ.get('S3_BUCKET_IN')
    test_file = open('tests/ladleSink/resources/test-file.pdf', 'rb').read()

    # Create the bucket
    s3_resource.create_bucket(Bucket=S3_BUCKET_IN)

    # Add a file
    s3_client.put_object(Bucket=S3_BUCKET_IN, Key="02fda3137e912f948c337263d790698a.pdf.raw", Body=test_file)

    # Construct a record from an event
    test_record = s3_object_created_event(S3_BUCKET_IN, "02fda3137e912f948c337263d790698a.pdf.raw")['Records'][0]

    # Run call with an event describing the file:
    success, key, raw_doc, msg = workers.get_created_object(test_record, S3_BUCKET_IN)

    assert success is True
    assert key == "02fda3137e912f948c337263d790698a.pdf.raw"
    assert raw_doc == test_file
    assert msg is None


def test_get_created_object_decodes_url_encoded_key_properly(normal_env, s3_resource, s3_client):
    S3_BUCKET_IN = os.environ.get('S3_BUCKET_IN')
    test_file = open('tests/ladleSink/resources/test-file.pdf', 'rb').read()

    # Create the bucket
    s3_resource.create_bucket(Bucket=S3_BUCKET_IN)

    # Add a file with space and special character that would be url-encoded in event object
    s3_client.put_object(Bucket=S3_BUCKET_IN, Key="Test Sübmission.pdf.raw", Body=test_file)

    # Construct a record from an event, using url-encoded string
    test_record = s3_object_created_event(S3_BUCKET_IN, "Test+S%C3%BCbmission.pdf.raw")['Records'][0]

    # Run call with an event describing the file:
    success, key, raw_doc, msg = workers.get_created_object(test_record, S3_BUCKET_IN)

    assert success is True
    assert key == "Test Sübmission.pdf.raw"
    assert raw_doc == test_file
    assert msg is None


def test_get_created_object_returns_appropriate_error_message_when_object_doesnt_exist(normal_env, s3_resource):
    S3_BUCKET_IN = os.environ.get('S3_BUCKET_IN')

    # Create the bucket but don't add a file
    s3_resource.create_bucket(Bucket=S3_BUCKET_IN)

    # Construct a record from an event
    test_record = s3_object_created_event(S3_BUCKET_IN, "02fda3137e912f948c337263d790698a.pdf.raw")['Records'][0]

    # Run call with an event describing the file:
    success, key, raw_doc, msg = workers.get_created_object(test_record, S3_BUCKET_IN)

    assert success is False
    assert key == "02fda3137e912f948c337263d790698a.pdf.raw"
    assert raw_doc is None
    assert msg[0:11] == f'Exception: '


def test_post_retrieved_object_sends_non_factiva_doc_to_regular_submission_endpoint(normal_env):
    DART_URL = os.environ.get('DART_URL')
    SUBMISSION_PORT = os.environ.get('SUBMISSION_PORT')
    SUBMISSION_ENDPOINT = os.environ.get('SUBMISSION_ENDPOINT')
    BAUTH_PASSWORD = os.environ.get('BAUTH_PASSWORD')
    BAUTH_USERNAME = os.environ.get('BAUTH_USERNAME')

    with mock.patch('dart_lambdas.ladleSink.workers.try_post') as try_post_mocker:

        def mock_try_post(url, port, endpoint, post_files, post_data, basic_auth, sleep_time, numtimes):
            assert post_files['file'][0] == "02fda3137e912f948c337263d790698a.pdf"
            assert post_files['file'][1] == b"this is a test"
            assert post_files['metadata'][0] is None
            assert post_files['metadata'][1] == "this is a test"
            assert post_files['metadata'][2] == "application/json"
            assert url == DART_URL
            assert port == SUBMISSION_PORT
            assert endpoint == SUBMISSION_ENDPOINT
            assert post_data is None
            assert basic_auth[0] == BAUTH_USERNAME
            assert basic_auth[1] == BAUTH_PASSWORD
            return True, '{ "document_id": "02fda3137e912f948c337263d790698a" }'

        try_post_mocker.side_effect = mock_try_post

        test_data = b"this is a test"
        filename = "02fda3137e912f948c337263d790698a.pdf"
        success, msg = workers.post_retrieved_object_and_metadata(filename, test_data, test_data.decode('utf-8'))
        try_post_mocker.assert_called()
        assert success is True
        assert msg == '{ "document_id": "02fda3137e912f948c337263d790698a" }'

def test_post_retrieved_object_sends_factiva_doc_to_factiva_submission_endpoint(normal_env):
    DART_URL = os.environ.get('DART_URL')
    SUBMISSION_PORT = os.environ.get('SUBMISSION_PORT')
    FACTIVA_SUBMISSION_ENDPOINT = os.environ.get('FACTIVA_SUBMISSION_ENDPOINT')
    BAUTH_PASSWORD = os.environ.get('BAUTH_PASSWORD')
    BAUTH_USERNAME = os.environ.get('BAUTH_USERNAME')

    with mock.patch('dart_lambdas.ladleSink.workers.try_post') as try_post_mocker:
        def mock_try_post(url, port, endpoint, post_files, post_data, basic_auth, sleep_time,
                          numtimes):
            assert post_files['file'][0] == "02fda3137e912f948c337263d790698a.factiva"
            assert post_files['file'][1] == b"this is a test"
            assert post_files['metadata'][0] is None
            assert post_files['metadata'][1] == "this is a test"
            assert post_files['metadata'][2] == "application/json"
            assert url == DART_URL
            assert port == SUBMISSION_PORT
            assert endpoint == FACTIVA_SUBMISSION_ENDPOINT
            assert post_data is None
            assert basic_auth[0] == BAUTH_USERNAME
            assert basic_auth[1] == BAUTH_PASSWORD
            return True, '{ "document_id": "02fda3137e912f948c337263d790698a" }'

        try_post_mocker.side_effect = mock_try_post

        test_data = b"this is a test"
        filename = "02fda3137e912f948c337263d790698a.factiva"
        success, msg = workers.post_retrieved_object_and_metadata(filename, test_data, test_data.decode('utf-8'))
        try_post_mocker.assert_called()
        assert success is True
        assert msg == '{ "document_id": "02fda3137e912f948c337263d790698a" }'


def test_move_processed_object_deletes_object_in_input_bucket_and_puts_it_in_output_bucket(normal_env, s3_resource, s3_client):
    S3_BUCKET_IN = os.environ.get('S3_BUCKET_IN')
    S3_BUCKET_PROCESSED = os.environ.get('S3_BUCKET_PROCESSED')
    test_file = open('tests/ladleSink/resources/test-file.pdf', 'rb').read()

    # Create the buckets
    s3_resource.create_bucket(Bucket=S3_BUCKET_IN)
    s3_resource.create_bucket(Bucket=S3_BUCKET_PROCESSED)

    # Add a file
    s3_client.put_object(Bucket=S3_BUCKET_IN, Key="input.pdf", Body=test_file)

    # Construct a record from an event
    test_record = s3_object_created_event(S3_BUCKET_IN, "input.pdf")['Records'][0]

    # Run call with an event describing the file:
    success, msg = workers.move_processed_object("input.pdf", S3_BUCKET_IN, "output.pdf", S3_BUCKET_PROCESSED)

    assert success is True
    assert msg == f"Successfully moved input.pdf from {S3_BUCKET_IN} to output.pdf in {S3_BUCKET_PROCESSED}"

    with pytest.raises(botocore.exceptions.ClientError):
        s3_client.get_object(Key="input.pdf", Bucket=S3_BUCKET_IN)

    try:
        s3_client.get_object(Key="output.pdf", Bucket=S3_BUCKET_PROCESSED)
    except botocore.exceptions.ClientError as e:
        pytest.fail(f"Did not put file in {S3_BUCKET_PROCESSED}")
