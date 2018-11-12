import json
import logging

import requests
from requests import RequestException

import boto3


def get_raw_metadata(path):
    try:
        r = requests.get('http://169.254.169.254' + path)
        r.raise_for_status()
    except RequestException as e:
        logging.exception(e)
        return ''

    return r.text


def get_metadata_field(path, field):
    raw = get_raw_metadata(path)
    if not raw:
        return ''

    try:
        response_json = json.loads(raw)
    except ValueError as e:
        logging.exception(e)
        return None

    return response_json[field]


account_id = get_metadata_field('/latest/meta-data/identity-credentials/ec2/info', 'AccountId')
role_name = get_raw_metadata('/latest/meta-data/iam/security-credentials/').split('\n')[0]

print('arn:aws:iam::{}:role/{}'.format(account_id, role_name))
