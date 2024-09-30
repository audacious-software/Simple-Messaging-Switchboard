def simple_data_export_fields(data_type):
    if data_type == 'simple_messaging.conversation_transcripts': # or link click export
        return [
            'Simple Messaging Switchboard: Channel',
        ]

    return []

def simple_data_export_field_values(data_type, message, extra_fields): # pylint: disable=invalid-name
    if data_type == 'simple_messaging.conversation_transcripts':
        values = {}

        for extra_field in extra_fields:
            if extra_field == 'Simple Messaging Switchboard: Channel':
                values[extra_field] = message.get('channel', None)

        return values

    return {}
