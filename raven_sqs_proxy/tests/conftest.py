"""
.. module: sqsproxy
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.
.. moduleauthor:: Mike Grima <mikegrima> @THISisPLACEHLDR
"""
import pytest
from moto.sqs import mock_sqs
import boto3


@pytest.fixture(scope='function')
def sqs():
    with mock_sqs():
        yield boto3.client('sqs', region_name="us-east-1")


@pytest.fixture(scope='function')
def sqs_queue(sqs):
    sqs.create_queue(QueueName="test-queue")

    return sqs


@pytest.fixture(scope='function')
def url(sqs_queue):
    return sqs_queue.get_queue_url(QueueName="test-queue",
                                   QueueOwnerAWSAccountId="123456789012")["QueueUrl"]


@pytest.fixture(scope="function")
def sqs_message(sqs_queue, url):
    sqs_queue.send_message(QueueUrl=url, MessageBody="hello")

    return sqs_queue.receive_message(QueueUrl=url)


class MockSentry:
    def __init__(self, status_code):
        self.status_code = status_code

    def status_code(self):
        return self.status_code


def mock_sentry(*args, **kwargs):
    if "fail" in args[0]:
        return MockSentry(404)

    return MockSentry(200)
