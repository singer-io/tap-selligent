campaign = {
    'type': ['object', 'null'],
    'properties': {
        'asset_id': {'type': 'integer'},
        'asset_name': {'type': 'string'},
        'modified_time': {'type': 'string'},
        'version_number': {'type': 'integer'},
    }
}

owner = {
    'type': ['object', 'null'],
    'properties': {
        'asset_id': {'type': 'integer'},
        'first_name': {'type': 'string'},
        'last_name': {'type': 'string'},
        'modified_time': {'type': 'string'},
    }
}

transactional_mailing = {
    'type': 'object',
    'properties': {
        'id': {
            'type': 'integer',
            'description': 'The asset_id of this mailing',
        },
        'approved': {'type': 'boolean'},
        'asset_name': {'type': 'string'},
        'campaign': campaign,
        'channel': {'type': 'string'},
        'compliance': {'type': 'boolean'},
        'mailing_priority': {'type': 'string'},
        'mailing_server_group': {'type': 'string'},
        'mailing_status': {'type': 'string'},
        'modified_time': {'type': 'string'},
        'owner': owner,
        'target': {
            'type': ['object', 'null'],
            'properties': {
                'asset_id': {'type': 'integer'},
                'asset_name': {'type': 'string'},
            }
        },
        'version_number': {'type': 'integer'}
    }
}

internal_datasource = {
    'type': 'object',
    'properties': {
        'id': {
            'type': 'integer',
            'description': 'The asset_id of this mailing',
        },
        'asset_name': {'type': 'string'},
        'asset_url': {'type': 'string'},
        'campaign': campaign,
        'cloud_sync': {'type': 'boolean'},
        'data_source_stat': {
            'type': 'object',
            'properties': {
                'num_total_rec': {'type': 'integer'}
            }
        },
        'modified_time': {'type': 'string'},
        'owner': owner,
        'version_number': {'type': 'integer'}
    }
}

extension_datasource = internal_datasource

source = {
    'type': ['object', 'null'],
    'properties': {
        'asset_id': {'type': 'integer'},
        'asset_name': {'type': 'string'},
        'data_source_type': {'type': 'string'},
        'version_number': {'type': 'integer'},
        'modified_time': {'type': 'string'},
    }
}

program = {
    'type': 'object',
    'properties': {
        'id': {
            'type': 'integer',
            'description': 'The asset_id of this mailing',
        },
        'asset_name': {'type': 'string'},
        'asset_url': {'type': 'string'},
        'campaign': campaign,
        'modified_time': {'type': 'string'},
        'owner': owner,
        'primary_source': source,
        'program_data_source': source,
        'status': {'type': 'string'},
        'type': {'type': 'string'},
    }
}

endpoint_to_schema_mapping = {
    'programs': program,
    'mailings/transactional': transactional_mailing,
    'data-sources/internal': internal_datasource,
    'data-sources/extension': extension_datasource,
}
