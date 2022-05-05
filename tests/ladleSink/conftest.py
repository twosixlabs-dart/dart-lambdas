import os
import pytest
import boto3
from moto import mock_s3

@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'

@pytest.fixture(scope='function')
def s3_resource(aws_credentials):
    with mock_s3():
        yield boto3.resource('s3', region_name='us-east-1')


@pytest.fixture(scope='function')
def s3_client(aws_credentials):
    with mock_s3():
        yield boto3.client('s3', region_name='us-east-1')


@pytest.fixture(scope='function')
def normal_env():
    os.environ['S3_BUCKET_IN'] = "test-bucket-in"
    os.environ['S3_BUCKET_PROCESSED'] = "test-bucket-processed"
    os.environ['LOGGING'] = "ON"
    os.environ['DART_URL'] = "0.0.0.0"
    os.environ['SUBMISSION_PORT'] = "100"
    os.environ['SUBMISSION_ENDPOINT'] = "/test/endpoint"
    os.environ['FACTIVA_SUBMISSION_ENDPOINT'] = "/test/factiva/endpoint"
    os.environ['BAUTH_USERNAME'] = "testusername"
    os.environ['BAUTH_PASSWORD'] = "testpassword"
