import json
import mock
import os
import botocore
import pytest

from dart_lambdas.ladleSink.ladle_sink import lambda_handler


def test_handler_gets_file_from_input_bucket_sends_it_to_ladle_then_moves_to_processed_bucket(normal_env, s3_resource, s3_client):
    S3_BUCKET_IN = os.environ.get('S3_BUCKET_IN')
    S3_BUCKET_PROCESSED = os.environ.get('S3_BUCKET_PROCESSED')
    DART_URL = os.environ.get('DART_URL')

    with mock.patch('dart_lambdas.ladleSink.workers.try_post') as try_post_mocker:
        test_file = open('tests/ladleSink/resources/test-file.pdf', 'rb').read()
        test_file_metadata = open('tests/ladleSink/resources/test-file-meta.json', 'rb').read()

        # Set up mock response to ladle call

        def mock_try_post(url, port, endpoint, post_files, post_data, basic_auth, sleep_time, numtimes):
            assert post_files['file'][1] == test_file
            return True, '{ "document_id": "02fda3137e912f948c337263d790698a" }'

        try_post_mocker.side_effect = mock_try_post

        # Create the bucket
        s3_resource.create_bucket(Bucket=S3_BUCKET_IN)
        s3_resource.create_bucket(Bucket=S3_BUCKET_PROCESSED)

        # Add a file
        s3_client.put_object(Bucket=S3_BUCKET_IN, Key="02fda3137e912f948c337263d790698a.pdf.raw", Body=test_file)
        s3_client.put_object(Bucket=S3_BUCKET_IN, Key="02fda3137e912f948c337263d790698a.meta", Body=test_file_metadata)

        # Run call with an event describing the file:
        result = lambda_handler(s3_object_created_event(S3_BUCKET_IN, "02fda3137e912f948c337263d790698a.pdf.raw"), None)

        assert json.loads(result['body']) == f'Successfully pulled 02fda3137e912f948c337263d790698a.pdf.raw from {S3_BUCKET_IN}, posted it to {DART_URL} as 02fda3137e912f948c337263d790698a.pdf, and moved it to {S3_BUCKET_PROCESSED} as 02fda3137e912f948c337263d790698a.pdf'
        assert result['statusCode'] == 200
        try_post_mocker.assert_called()

        with pytest.raises(botocore.exceptions.ClientError):
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.pdf.raw", Bucket=S3_BUCKET_IN)

        with pytest.raises(botocore.exceptions.ClientError):
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.meta", Bucket=S3_BUCKET_IN)

        try:
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.pdf", Bucket=S3_BUCKET_PROCESSED)
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.meta", Bucket=S3_BUCKET_PROCESSED)
        except s3_client.exceptions.ClientException as e:
            pytest.fail(f"Did not put file in {S3_BUCKET_PROCESSED}")


def test_handler_gets_file_from_input_bucket_sends_it_to_ladle_then_moves_to_processed_bucket_with_doc_id_from_ladle(normal_env, s3_resource, s3_client):
    S3_BUCKET_IN = os.environ.get('S3_BUCKET_IN')
    S3_BUCKET_PROCESSED = os.environ.get('S3_BUCKET_PROCESSED')
    DART_URL = os.environ.get('DART_URL')

    with mock.patch('dart_lambdas.ladleSink.workers.try_post') as try_post_mocker:
        test_file = open('tests/ladleSink/resources/test-file.pdf', 'rb').read()
        test_file_metadata = open('tests/ladleSink/resources/test-file-meta.json', 'rb').read()

        # Set up mock response to ladle call

        def mock_try_post(url, port, endpoint, post_files, post_data, basic_auth, sleep_time, numtimes):
            assert post_files['file'][1] == test_file
            return True, '{ "document_id": "Z2fda3137e912f948c337263d790698Z" }' # Note first and last letters differ from file below

        try_post_mocker.side_effect = mock_try_post

        # Create the bucket
        s3_resource.create_bucket(Bucket=S3_BUCKET_IN)
        s3_resource.create_bucket(Bucket=S3_BUCKET_PROCESSED)

        # Add a file
        s3_client.put_object(Bucket=S3_BUCKET_IN, Key="some.file.name.pdf.raw", Body=test_file)
        s3_client.put_object(Bucket=S3_BUCKET_IN, Key="some.file.name.meta", Body=test_file_metadata)

        # Run call with an event describing the file:
        result = lambda_handler(s3_object_created_event(S3_BUCKET_IN, "some.file.name.pdf.raw"), None)

        assert json.loads(result['body']) == f'Successfully pulled some.file.name.pdf.raw from {S3_BUCKET_IN}, posted it to {DART_URL} as some.file.name.pdf, and moved it to {S3_BUCKET_PROCESSED} as Z2fda3137e912f948c337263d790698Z.pdf'
        assert result['statusCode'] == 200
        try_post_mocker.assert_called()

        with pytest.raises(botocore.exceptions.ClientError):
            s3_client.get_object(Key="some.file.name.pdf.raw", Bucket=S3_BUCKET_IN)

        with pytest.raises(botocore.exceptions.ClientError):
            s3_client.get_object(Key="some.file.name.meta", Bucket=S3_BUCKET_IN)

        try:
            s3_client.get_object(Key="Z2fda3137e912f948c337263d790698Z.pdf", Bucket=S3_BUCKET_PROCESSED)
            s3_client.get_object(Key="Z2fda3137e912f948c337263d790698Z.meta", Bucket=S3_BUCKET_PROCESSED)
        except s3_client.exceptions.ClientError as e:
            pytest.fail(f"Did not put file in {S3_BUCKET_PROCESSED}")


def test_handler_gets_file_without_docid_filename_with_url_encoded_filename_from_input_bucket_sends_it_to_ladle_then_moves_to_processed_bucket(normal_env, s3_resource, s3_client):
    S3_BUCKET_IN = os.environ.get('S3_BUCKET_IN')
    S3_BUCKET_PROCESSED = os.environ.get('S3_BUCKET_PROCESSED')
    DART_URL = os.environ.get('DART_URL')

    with mock.patch('dart_lambdas.ladleSink.workers.try_post') as try_post_mocker:
        test_file = open('tests/ladleSink/resources/test-file.pdf', 'rb').read()
        test_file_metadata = open('tests/ladleSink/resources/test-file-meta.json', 'rb').read()

        # Set up mock response to ladle call

        def mock_try_post(url, port, endpoint, post_files, post_data, basic_auth, sleep_time, numtimes):
            assert post_files['file'][1] == test_file
            return True, '{ "document_id": "02fda3137e912f948c337263d790698a" }'

        try_post_mocker.side_effect = mock_try_post

        # Create the bucket
        s3_resource.create_bucket(Bucket=S3_BUCKET_IN)
        s3_resource.create_bucket(Bucket=S3_BUCKET_PROCESSED)

        # Add a file
        s3_client.put_object(Bucket=S3_BUCKET_IN, Key="Test Sübmission.Pdf.raw", Body=test_file)
        s3_client.put_object(Bucket=S3_BUCKET_IN, Key="Test Sübmission.meta", Body=test_file_metadata)

        # Run call with an event describing the file; even uses url-encoding for key:
        result = lambda_handler(s3_object_created_event(S3_BUCKET_IN, "Test+S%C3%BCbmission.Pdf.raw"), None)

        assert json.loads(result['body']) == f'Successfully pulled Test Sübmission.Pdf.raw from {S3_BUCKET_IN}, posted it to {DART_URL} as Test Sübmission.Pdf, and moved it to {S3_BUCKET_PROCESSED} as 02fda3137e912f948c337263d790698a.pdf'
        assert result['statusCode'] == 200
        try_post_mocker.assert_called()

        with pytest.raises(botocore.exceptions.ClientError):
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.pdf.raw", Bucket=S3_BUCKET_IN)

        with pytest.raises(botocore.exceptions.ClientError):
            s3_client.get_object(Key="Test Sübmission.Pdf.raw", Bucket=S3_BUCKET_IN)

        with pytest.raises(botocore.exceptions.ClientError):
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.meta", Bucket=S3_BUCKET_IN)

        with pytest.raises(botocore.exceptions.ClientError):
            s3_client.get_object(Key="Test Sübmission.meta", Bucket=S3_BUCKET_IN)

        try:
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.pdf", Bucket=S3_BUCKET_PROCESSED)
        except s3_client.exceptions.ClientError as e:
            pytest.fail(f"Did not put file in {S3_BUCKET_PROCESSED}")

        try:
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.meta", Bucket=S3_BUCKET_PROCESSED)
        except s3_client.exceptions.ClientError as e:
            pytest.fail(f"Did not put file in {S3_BUCKET_PROCESSED}")


def test_handler_does_not_send_file_that_fails_on_ladle_to_processed_and_keeps_it_in_input_bucket(normal_env, s3_resource, s3_client):
    S3_BUCKET_IN = os.environ.get('S3_BUCKET_IN')
    S3_BUCKET_PROCESSED = os.environ.get('S3_BUCKET_PROCESSED')

    with mock.patch('dart_lambdas.ladleSink.workers.try_post') as try_post_mocker:
        test_file = open('tests/ladleSink/resources/test-file.pdf', 'rb').read()
        test_file_metadata = open('tests/ladleSink/resources/test-file-meta.json', 'rb').read()

        # Set up mock response to ladle call
        def mock_try_post(url, port, endpoint, post_files, post_data, basic_auth, sleep_time, numtimes):
            assert post_files['file'][1] == test_file
            return False, "mocked ladle failure"

        try_post_mocker.side_effect = mock_try_post

        # Create the bucket
        s3_resource.create_bucket(Bucket=S3_BUCKET_IN)
        s3_resource.create_bucket(Bucket=S3_BUCKET_PROCESSED)

        # Add a file
        s3_client.put_object(Bucket=S3_BUCKET_IN, Key="02fda3137e912f948c337263d790698a.pdf.raw", Body=test_file)
        s3_client.put_object(Bucket=S3_BUCKET_IN, Key="02fda3137e912f948c337263d790698a.meta", Body=test_file_metadata)


        # Run call with an event describing the file:
        result = lambda_handler(s3_object_created_event(S3_BUCKET_IN, "02fda3137e912f948c337263d790698a.pdf.raw"), None)

        assert json.loads(result['body']) == f"Unable to submit 02fda3137e912f948c337263d790698a.pdf.raw to ladle as 02fda3137e912f948c337263d790698a.pdf: mocked ladle failure"
        assert result['statusCode'] == 500
        try_post_mocker.assert_called()

        with pytest.raises(botocore.exceptions.ClientError):
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.pdf.raw", Bucket=S3_BUCKET_PROCESSED)

        with pytest.raises(botocore.exceptions.ClientError):
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.meta", Bucket=S3_BUCKET_PROCESSED)

        try:
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.pdf.raw", Bucket=S3_BUCKET_IN)
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.meta", Bucket=S3_BUCKET_IN)
        except botocore.exceptions.ClientError as e:
            pytest.fail(f"Did not keep file in {S3_BUCKET_IN}")

def test_handler_does_nothing_with_metadata_file(normal_env, s3_resource, s3_client):
    S3_BUCKET_IN = os.environ.get('S3_BUCKET_IN')
    S3_BUCKET_PROCESSED = os.environ.get('S3_BUCKET_PROCESSED')

    with mock.patch('dart_lambdas.ladleSink.workers.try_post') as try_post_mocker:
        test_file = open('tests/ladleSink/resources/test-file.pdf', 'rb').read()

        # Set up mock response to ladle call

        def mock_try_post(url, port, endpoint, post_files, post_data, basic_auth, sleep_time, numtimes):
            assert post_files['file'][1] == test_file
            return True, '{ "document_id": "02fda3137e912f948c337263d790698a" }'

        try_post_mocker.side_effect = mock_try_post

        # Create the bucket
        s3_resource.create_bucket(Bucket=S3_BUCKET_IN)
        s3_resource.create_bucket(Bucket=S3_BUCKET_PROCESSED)

        # Add a file
        s3_client.put_object(Bucket=S3_BUCKET_IN, Key="02fda3137e912f948c337263d790698a.meta", Body=test_file)

        # Run call with an event describing the file:
        result = lambda_handler(s3_object_created_event(S3_BUCKET_IN, "02fda3137e912f948c337263d790698a.meta"), None)

        assert json.loads(result['body']) == "metadata file (02fda3137e912f948c337263d790698a.meta): no need to pass to ladle"
        assert result['statusCode'] == 200
        assert not try_post_mocker.called

        with pytest.raises(botocore.exceptions.ClientError):
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.meta", Bucket=S3_BUCKET_PROCESSED)

        try:
            s3_client.get_object(Key="02fda3137e912f948c337263d790698a.meta", Bucket=S3_BUCKET_IN)
        except botocore.exceptions.ClientError as e:
            pytest.fail(f"Should not have put file in {S3_BUCKET_PROCESSED}")


def test_handler_errors_out_when_metadata_file_is_absent(normal_env, s3_resource, s3_client):
    S3_BUCKET_IN = os.environ.get('S3_BUCKET_IN')
    S3_BUCKET_PROCESSED = os.environ.get('S3_BUCKET_PROCESSED')

    test_file = open('tests/ladleSink/resources/test-file.pdf', 'rb').read()

    # Create the bucket
    s3_resource.create_bucket(Bucket=S3_BUCKET_IN)
    s3_resource.create_bucket(Bucket=S3_BUCKET_PROCESSED)

    # Add a file
    s3_client.put_object(Bucket=S3_BUCKET_IN, Key="02fda3137e912f948c337263d790698a.pdf.raw", Body=test_file)

    # Run call with an event describing the file:
    result = lambda_handler(s3_object_created_event(S3_BUCKET_IN, "02fda3137e912f948c337263d790698a.pdf.raw"), None)

    assert f"Unable to retrieve 02fda3137e912f948c337263d790698a.meta from {S3_BUCKET_IN}" in json.loads(result['body'])
    assert result['statusCode'] == 500

    with pytest.raises(botocore.exceptions.ClientError):
        s3_client.get_object(Key="02fda3137e912f948c337263d790698a.pdf", Bucket=S3_BUCKET_PROCESSED)

    with pytest.raises(botocore.exceptions.ClientError):
        s3_client.get_object(Key="02fda3137e912f948c337263d790698a.meta", Bucket=S3_BUCKET_PROCESSED)

    with pytest.raises(botocore.exceptions.ClientError):
        s3_client.get_object(Key="02fda3137e912f948c337263d790698a.meta", Bucket=S3_BUCKET_IN)

    try:
        s3_client.get_object(Key="02fda3137e912f948c337263d790698a.pdf.raw", Bucket=S3_BUCKET_IN)
    except botocore.exceptions.ClientError as e:
        pytest.fail(f"Did not keep file in {S3_BUCKET_IN}")


def s3_object_created_event(bucket_name, key):
    # NOTE: truncated event object shown here
    return {
      "Records": [
        {
          "s3": {
            "object": {
              "key": key,
            },
            "bucket": {
              "name": bucket_name,
            },
          },
        }
      ]
    }
