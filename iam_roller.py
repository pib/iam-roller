import argparse
import json
import logging

import requests
from requests import RequestException

import boto3
from kubernetes import client, config


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


def get_role_arn():
    account_id = get_metadata_field('/latest/dynamic/instance-identity/document', 'accountId')
    role_name = get_raw_metadata('/latest/meta-data/iam/security-credentials/').split('\n')[0]

    role_arn = 'arn:aws:iam::{}:role/{}'.format(account_id, role_name)
    return role_arn


def assume_role(role_arn):
    sts = boto3.client('sts')
    res = sts.assume_role(RoleArn=role_arn, RoleSessionName='iam_roller', DurationSeconds=1800)
    return res


def make_creds_file(credentials):
    creds_file = '''
[default]
aws_access_key_id={AccessKeyId}
aws_secret_access_key={SecretAccessKey}
aws_session_token={SessionToken}
'''.format(**credentials)
    return creds_file


def write_secret(namespace, name, data):
    kapi = client.CoreV1Api()
    sec = client.V1Secret()
    sec.metadata = client.V1ObjectMeta(name=name)
    sec.type = 'Opaque'
    sec.string_data = data

    res = kapi.create_namespaced_secret(namespace=namespace, body=sec)
    return res


def run(namespace, name):
    config.load_incluster_config()

    role_arn = get_role_arn()
    logging.info('Generating temporary credentials for role %s', role_arn)
    creds = assume_role(role_arn)
    creds_file = make_creds_file(creds['Credentials'])

    res = write_secret(namespace, name, data={'credentials': creds_file})
    logging.info('Response: %s', res)


def main():
    parser = argparse.ArgumentParser(
        description='Grab a rolling short-lived IAM key/secret and save it in a Kubernetes secret.')
    parser.add_argument('--namespace', required=True,
                        help="Namespace in which secret should be stored")
    parser.add_argument('--name', required=True,
                        help="Name under which the secret should be stored")

    args = parser.parse_args()

    run(args.namespace, args.name)

if __name__ == '__main__':
    main()
