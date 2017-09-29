"""
.. module: sqsproxy
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.
.. moduleauthor:: Mike Grima <mikegrima> @THISisPLACEHLDR
"""
import boto3
import click
import requests
import base64
import click_log
import json
import logging
import sys
import signal

from retrying import retry, RetryError
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
click_log.basic_config(logger)


SQS_WAIT_TIME_SECONDS = 20


# For graceful exits...
def handle_exit(signal, frame):
    logger.info("[!] Received signal to exit... Exiting...")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_exit)


def validate_region(ctx, param, value):
    """Validate that a proper AWS region was passed in"""
    all_regions = boto3.session.Session().get_available_regions("sqs")

    if value not in all_regions:
        raise click.BadParameter("Invalid region passed in. Must be one of: {}".format(", ".join(all_regions)))

    return value


def retry_if_client_error(exception):
    """Retry function to detect if the exception is a boto client error"""
    return isinstance(exception, ClientError)


@retry(retry_on_exception=retry_if_client_error, stop_max_attempt_number=5, wait_fixed=3000, wrap_exception=True)
def receive_messages(client, url):
    """
    Listens to the SQS queue and retrieves messages.
    :param client:
    :param url:
    :return:
    """
    messages = client.receive_message(QueueUrl=url, WaitTimeSeconds=SQS_WAIT_TIME_SECONDS)

    if not messages.get("Messages"):
        logger.debug("[><] No messages received.  Listening for another {} seconds...".format(SQS_WAIT_TIME_SECONDS))
        messages["Messages"] = []

    return messages


@retry(retry_on_exception=retry_if_client_error, stop_max_attempt_number=5, wait_fixed=3000, wrap_exception=True)
def delete_message(client, url, receipt_handle):
    """Deletes message from SQS because it was successfully processed"""
    client.delete_message(QueueUrl=url, ReceiptHandle=receipt_handle)


@retry(stop_max_attempt_number=5, wait_fixed=3000, wrap_exception=True)
def send_to_sentry(sentry_url, headers, data):
    """
    Send the message over to Sentry.
    :param sentry_url: This is the URL of the Sentry server
    :param headers: This contains all the headers required to send over to Sentry
    :param data: The actual payload to send over to Sentry
    :return:
    """
    result = requests.post(sentry_url, headers=headers, data=data)

    if result.status_code != 200:
        raise ValueError("Invalid response code from Sentry: {}".format(result.status_code))


def sqs_loop(client, url):
    """
    This is the main logic proxy-loop. This will keep polling and proxying data to Sentry.
    :param client:
    :param url:
    :return:
    """
    while True:
        logger.debug("[ ] Polling for messages...")

        # Get the messages:
        try:
            messages = receive_messages(client, url)
        except RetryError as re:
            logger.error("Encountered too many Boto ClientErrors while fetching messages... Exiting...")
            logger.exception(re.last_attempt.value)
            sys.exit(-1)

        # Place each message into Sentry:
        for message in messages["Messages"]:
            body = None
            try:
                body = json.loads(message["Body"])

            except json.decoder.JSONDecodeError as _:
                logger.error("Error decoding message sent. Going to delete the message and skip...")

            if body:
                sentry_url = body["url"]
                headers = body["headers"]
                data = base64.b64decode(body["data"])

                # Send it over!
                try:
                    logger.debug("[ ] Sending message to Sentry at URL: {}".format(sentry_url))
                    send_to_sentry(sentry_url, headers, data)
                    logger.debug("[+] Successfully sent message to Sentry at URL: {}".format(sentry_url))
                except RetryError as re:
                    logger.error("Encountered too many errors sending data to Sentry with URL: {}. "
                                 "Going to skip and delete message from SQS...".format(sentry_url))
                    logger.exception(re.last_attempt.value)

            # Delete the message from SQS:
            try:
                logger.debug("[ ] Deleting message from SQS with Receipt Handle: {}".format(message["ReceiptHandle"]))
                delete_message(client, url, message["ReceiptHandle"])
                logger.debug("[-] Deleted message from SQS with Receipt Handle: {}".format(message["ReceiptHandle"]))
            except RetryError as re:
                logger.error("Encountered too many Boto ClientErrors while fetching messages... Exiting...")
                logger.exception(re.last_attempt.value)
                sys.exit(-1)


@click.command()
@click.option("--queue-name", type=click.STRING, required=True, help="The name of the SQS queue")
@click.option("--queue-region", type=click.STRING, callback=validate_region, required=True,
              help="The region where the SQS queue lives")
@click.option("--queue-account", type=click.STRING, required=True, help="The AWS account that contains the SQS queue")
@click.option("--log-level", type=click.STRING, required=False, help="The log level for the application - DEFAULT INFO",
              default="INFO")
def cli(queue_name, queue_region, queue_account, log_level):
    """
    Runs the Raven SQS Proxy service -- this will just poll SQS and will proxy the messages to Sentry

    :param queue_name - The name of the SQS queue
    :return:
    """
    # Set the log level:
    logger.setLevel(log_level)

    logger.info("[@] Raven SQS Poller is now running against queue Name/Account/Region: "
                "{name}/{account}/{region}".format(name=queue_name, account=queue_account, region=queue_region))

    # Create the SQS client:
    client = boto3.client("sqs", region_name=queue_region)

    logger.debug("[ ] Fetching the URL of the SQS Queue...")
    try:
        url = client.get_queue_url(QueueName=queue_name, QueueOwnerAWSAccountId=queue_account)["QueueUrl"]

    except ClientError as ce:
        logger.error("[X] Unable to get queue URL. Cannot continue. Exception is below:")
        raise ce

    logger.debug("[+] Fetched the Queue URL: {}".format(url))

    logger.info("[-->] Now monitoring SQS for messages to send over to Sentry...")
    sqs_loop(client, url)
