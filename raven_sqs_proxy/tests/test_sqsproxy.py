"""
.. module: sqsproxy
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.
.. moduleauthor:: Mike Grima <mikegrima> @THISisPLACEHLDR
"""
import pytest
from botocore.exceptions import ClientError
from retrying import RetryError
import mock

from raven_sqs_proxy.tests.conftest import mock_sentry


def test_validate_region():
    from raven_sqs_proxy.sqsproxy import validate_region
    import click

    assert validate_region(None, None, "us-east-1") == "us-east-1"

    with pytest.raises(click.BadParameter) as _:
        validate_region(None, None, "LOL")


def test_retry_if_client_error():
    from raven_sqs_proxy.sqsproxy import retry_if_client_error
    assert not retry_if_client_error(Exception())
    assert retry_if_client_error(ClientError({"Error": {}}, "SendMessage"))


def test_receive_messages(sqs_queue, url):
    import raven_sqs_proxy
    from raven_sqs_proxy.sqsproxy import receive_messages
    raven_sqs_proxy.sqsproxy.SQS_WAIT_TIME_SECONDS = 0

    result = receive_messages(sqs_queue, url)
    assert not result["Messages"]

    with pytest.raises(RetryError) as _:
        receive_messages(sqs_queue, "https://LOLNO")


def test_delete_messages(sqs_queue, url, sqs_message):
    from raven_sqs_proxy.sqsproxy import delete_message

    delete_message(sqs_queue, url, sqs_message["Messages"][0]["ReceiptHandle"])

    with pytest.raises(RetryError) as _:
        delete_message(sqs_queue, "https://LOLNO", sqs_message["Messages"][0]["ReceiptHandle"])


@mock.patch("requests.post", side_effect=mock_sentry)
def test_send_to_sentry(mock_post):
    from raven_sqs_proxy.sqsproxy import send_to_sentry

    headers = {}
    data = {"LOL": "HAY"}

    send_to_sentry("pass", headers, data)

    with pytest.raises(RetryError) as _:
        send_to_sentry("fail", headers, data)

