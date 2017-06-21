#!/usr/bin/env python3

import argparse
import json

import requests
import singer

import tap_selligent.schemas


logger = singer.get_logger()

BASE_URL = 'https://backstage.taboola.com'


def request(url, config, params={}):
    user_agent = config['user_agent']
    api_key = config['api_key']
    organization = config['organization']

    logger.info("Making request: GET {} {}".format(url, params))

    try:
        response = requests.get(
            url,
            headers={'Authorization': api_key,
                     'X-Organization': organization,
                     'Accept': 'application/json',
                     'User-Agent': user_agent},
            params=params)

    except BaseException as e:
        logger.exception(e)
        raise e

    logger.info("Got response code: {}".format(response.status_code))

    response.raise_for_status()
    return response


def fetch_transactional_mailings(config, state):
    return fetch(config, state, endpoint='mailings/transactional')


def fetch_programs(config, state):
    return fetch(config, state, endpoint='programs')


def fetch_internal_datasources(config, state):
    return fetch(config, state, endpoint='data-sources/internal')


def fetch_extension_datasources(config, state):
    return fetch(config, state, endpoint='data-sources/extension')


def fetch(config, state, endpoint):
    url = '{}/sm/rest/v1/{}/'.format(config['base_url'], endpoint)

    params = {
        'page': 1,
        'limit': 10000,
        'order': 'modified_time',
        'sort': 'asc'
    }

    result = request(
        url,
        config,
        params)

    return result.json()['data']


def fetch_one(config, state, endpoint, pk):
    url = '{}/sm/rest/v1/{}/{}'.format(config['base_url'], endpoint, pk)

    params = {
        'page': 1,
        'limit': 10000,
        'order': 'modified_time',
        'sort': 'asc'
    }

    result = request(
        url,
        config,
        params)

    return result.json()


def add_timezone(dt):
    return '{}Z'.format(dt)


def handle_nested_timestamps(data):
    if data.get('owner'):
        data['owner']['modified_time'] = \
            add_timezone(data['owner']['modified_time'])

    if data.get('campaign'):
        data['campaign']['modified_time'] = \
            add_timezone(data['campaign']['modified_time'])

    if data.get('primary_source'):
        data['primary_source']['modified_time'] = \
            add_timezone(data['primary_source']['modified_time'])

    if data.get('program_data_source'):
        data['program_data_source']['modified_time'] = \
            add_timezone(data['program_data_source']['modified_time'])

    return data


def parse_transactional_mailing(mailing):
    to_return = {
        'id': mailing.get('asset_id'),
        'approved': mailing.get('approved'),
        'asset_name': mailing.get('asset_name'),
        'asset_url': mailing.get('asset_url'),
        'campaign': mailing.get('campaign'),
        'channel': mailing.get('channel'),
        'compliance': mailing.get('compliance'),
        'mailing_priority': mailing.get('mailing_priority'),
        'mailing_server_group': mailing.get('mailing_server_group'),
        'mailing_status': mailing.get('mailing_status'),
        'modified_time': add_timezone(mailing.get('modified_time')),
        'owner': mailing.get('owner'),
        'target': mailing.get('target'),
        'version_number': mailing.get('version_number'),
    }

    return handle_nested_timestamps(to_return)


def parse_internal_datasource(datasource):
    to_return = {
        'id': datasource.get('asset_id'),
        'asset_name': datasource.get('asset_name'),
        'asset_url': datasource.get('asset_url'),
        'campaign': datasource.get('campaign'),
        'cloud_sync': datasource.get('cloud_sync'),
        'data_source_stat': datasource.get('data_source_stat'),
        'data_source_type': datasource.get('data_source_type'),
        'modified_time': add_timezone(datasource.get('modified_time')),
        'owner': datasource.get('owner'),
        'version_number': datasource.get('version_number')
    }

    return handle_nested_timestamps(to_return)


def parse_program(program):
    to_return = {
        'id': program.get('asset_id'),
        'asset_name': program.get('asset_name'),
        'asset_url': program.get('asset_url'),
        'campaign': program.get('campaign'),
        'modified_time': add_timezone(program.get('modified_time')),
        'owner': program.get('owner'),
        'primary_source': program.get('primary_source'),
        'program_data_source': program.get('program_data_source'),
        'status': program.get('status'),
        'version_number': program.get('version_number'),
    }

    return handle_nested_timestamps(to_return)


def sync(config, state, endpoint, parser):
    schema = tap_selligent.schemas.endpoint_to_schema_mapping[endpoint]

    singer.write_schema(
        endpoint,
        schema,
        key_properties=['id'])

    results = fetch(config, state, endpoint)

    for result in results:
        singer.write_records(
            endpoint,
            [parser(result)])


def sync_transactional_mailings(config, state):
    return sync(
        config, state,
        endpoint='mailings/transactional',
        parser=parse_transactional_mailing)


def sync_internal_datasources(config, state):
    return sync(
        config, state,
        endpoint='data-sources/internal',
        parser=parse_internal_datasource)


def sync_extension_datasources(config, state):
    return sync(
        config, state,
        endpoint='data-sources/extension',
        parser=parse_internal_datasource)


def sync_programs(config, state):
    return sync(
        config, state,
        endpoint='programs',
        parser=parse_program)


def validate_config(config):
    required_keys = ['organization', 'api_key', 'base_url']
    missing_keys = []
    null_keys = []
    has_errors = False

    for required_key in required_keys:
        if required_key not in config:
            missing_keys.append(required_key)

        elif config.get(required_key) is None:
            null_keys.append(required_key)

    if len(missing_keys) > 0:
        logger.fatal("Config is missing keys: {}"
                     .format(", ".join(missing_keys)))
        has_errors = True

    if len(null_keys) > 0:
        logger.fatal("Config has null keys: {}"
                     .format(", ".join(null_keys)))
        has_errors = True

    if has_errors:
        raise RuntimeError


def load_config(filename):
    config = {}

    try:
        with open(filename) as f:
            config = json.load(f)
    except:
        logger.fatal("Failed to decode config file. Is it valid json?")
        raise RuntimeError

    validate_config(config)

    return config


def load_state(filename):
    if filename is None:
        return {}

    try:
        with open(filename) as f:
            return json.load(f)
    except:
        logger.fatal("Failed to decode state file. Is it valid json?")
        raise RuntimeError


def do_sync(args):
    logger.info("Starting sync.")

    config = load_config(args.config)
    state = load_state(args.state)

    sync_transactional_mailings(config, state)
    sync_internal_datasources(config, state)
    sync_extension_datasources(config, state)
    sync_programs(config, state)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c', '--config', help='Config file', required=True)
    parser.add_argument(
        '-s', '--state', help='State file')

    args = parser.parse_args()

    try:
        do_sync(args)
    except RuntimeError:
        logger.fatal("Run failed.")
        exit(1)


if __name__ == '__main__':
    main()
