# pylint: disable=line-too-long, no-member, len-as-condition, import-outside-toplevel

import json

from simple_dashboard.models import DashboardSignal

from .models import Channel

def dashboard_signals():
    signals = []

    for channel in Channel.objects.filter(is_enabled=True):
        configuration = json.loads(channel.configuration)

        signals.append({
            'name': 'Switchboard: %s (%s)' % (configuration.get('phone_number', ''), channel.channel_type.name),
            'refresh_interval': 1800,
            'configuration': {
                'widget_columns': 6,
                'active': True,
                'channel_id': channel.pk
            }
        })

    return signals

def dashboard_template(signal_name):
    if signal_name.startswith('Switchboard:'):
        signal = DashboardSignal.objects.filter(name=signal_name).first()

        channel = Channel.objects.filter(pk=signal.configuration['channel_id']).first()

        configuration = json.loads(channel.configuration)

        if signal is not None and channel is not None:
            if channel.channel_type.package_name == 'simple_messaging_twilio':
                try:
                    from simple_messaging_twilio import dashboard_api

                    return dashboard_api.dashboard_template('Twilio: %s' % configuration.get('phone_number', ''))
                except ImportError:
                    pass
                except AttributeError:
                    pass

            if channel.channel_type.package_name == 'simple_messaging_azure':
                try:
                    from simple_messaging_twilio import dashboard_api

                    return dashboard_api.dashboard_template('Azure: %s' % configuration.get('phone_number', ''))
                except ImportError:
                    pass
                except AttributeError:
                    pass

    return None

def update_dashboard_signal_value(signal_name):
    if signal_name.startswith('Switchboard:'):
        signal = DashboardSignal.objects.filter(name=signal_name).first()

        channel = Channel.objects.filter(pk=signal.configuration['channel_id']).first()

        configuration = json.loads(channel.configuration)

        if signal is not None and channel is not None:
            if channel.channel_type.package_name == 'simple_messaging_twilio':
                try:
                    from simple_messaging_twilio import dashboard_api

                    client_id = configuration.get('client_id', 'missing-client-id')
                    auth_token = configuration.get('auth_token', 'missing-auth-token')
                    phone_number = configuration.get('phone_number', 'missing-phone-number')

                    root_client_id = configuration.get('root_client_id', 'missing-phone-number')
                    root_auth_token = configuration.get('root_auth_token', 'missing-phone-number')

                    return dashboard_api.update_dashboard_signal_value('Twilio: %s' % configuration.get('phone_number', ''), client_id=client_id, auth_token=auth_token, phone_number=phone_number, root_client_id=root_client_id, root_auth_token=root_auth_token)
                except ImportError:
                    pass
                except AttributeError:
                    pass

            if channel.channel_type.package_name == 'simple_messaging_azure':
                try:
                    from simple_messaging_twilio import dashboard_api

                    return None # dashboard_api.dashboard_template('Azure: %s' % configuration.get('phone_number', ''))
                except ImportError:
                    pass
                except AttributeError:
                    pass

    return None
