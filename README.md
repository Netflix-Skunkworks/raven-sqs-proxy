# Sentry/Raven SQS Proxy

[![Build Status](https://travis-ci.org/Netflix-Skunkworks/raven-sqs-proxy.svg?branch=master)](https://travis-ci.org/Netflix-Skunkworks/raven-sqs-proxy)

## About
This is a very simple Python project that polls SQS for Sentry messages and then proxies them over to a Sentry instance.

This is based on the implementation of the Sentry.IO `SQSTransport` as implemented in [this PR to raven-python](https://github.com/getsentry/raven-python/pull/1095).

## How to use:
The first part in using this is to make use of the Sentry `SQSTransport` implemented in the [getsentry/raven-python](https://github.com/getsentry/raven-python) 
project.

This will have an instance, lambda function, or anything with AWS credentials to an SQS queue to forward all Sentry messages to SQS. This project will then
listen for those messages on the queue and simply proxy them over to Sentry for storage.

## Required Items:
For sending to the SQS queue, you will need the following:
1. An SQS queue
1. An IAM role with the following permissions to the SQS queue in question:
    ```
    sqs:GetQueueUrl
    sqs:SendMessage
    ```
1. A Sentry DSN
1. Python code that creates a Sentry client that looks similar to this:
    ```
    from raven.base import Client
    from raven.transport.sqs import SQSTransport
    
    # SQS details that are required are:
    # 1. `sqs_region`
    # 2. `sqs_account` This is the 12 digit AWS account number
    # 3. `sqs_name` 
    
    sentry_client = Client(dsn="https://some-sentry-dsn?sqs_region=REGION&sqs_account=ACCOUNT_NUMsqs_name=QUEUE_NAME",
                           transport=SQSTransport)
    
    ```

For retrieving messages:
1. Access to the SQS queue the source app above is sending to. This will need the following permissions against the queue:
    ```
    sqs:GetQueueUrl
    sqs:SendMessage
    sqs:DeleteMessage
    ```
1. Network-level access to the Sentry instance


## Installation:
1. `pip` install this
1. Make a Python 3 virtual environment
1. Run `sqsproxy` with the required parameters

That's it.
