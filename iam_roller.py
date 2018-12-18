import argparse
import logging

import boto3
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logging.basicConfig()
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)


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

    try:
        log.info("Attempting to create %s in namespace %s", name, namespace)
        res = kapi.create_namespaced_secret(namespace=namespace, body=sec)
    except ApiException as e:
        if e.status != 409:
            raise
        log.info("Secret already exists, replacing instead")
        res = kapi.replace_namespaced_secret(name=name, namespace=namespace, body=sec)
    return res


def run(role_arn, namespace, name):

    log.info('Generating temporary credentials for role %s', role_arn)
    creds = assume_role(role_arn)
    creds_file = make_creds_file(creds['Credentials'])

    config.load_incluster_config()
    res = write_secret(namespace, name, data={'credentials': creds_file})
    log.debug('Response: %s', res)


def main():
    parser = argparse.ArgumentParser(
        description='Grab a rolling short-lived IAM key/secret and save it in a Kubernetes secret.')
    parser.add_argument('--namespace', required=True,
                        help="Namespace in which secret should be stored")
    parser.add_argument('--name', required=True,
                        help="Name under which the secret should be stored")
    parser.add_argument('--role-arn', required=True,
                        help="ARN of the IAM Role to assume")

    args = parser.parse_args()

    run(args.role_arn, args.namespace, args.name)


if __name__ == '__main__':
    log.info("start")
    main()
