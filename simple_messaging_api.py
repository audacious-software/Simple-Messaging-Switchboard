# pylint: disable=line-too-long, no-member

import importlib
import json

from django.conf import settings

from simple_messaging.models import IncomingMessage, OutgoingMessage

from .models import Channel

def channel_for_message(outgoing_message):
    outgoing_channel = None

    for app in settings.INSTALLED_APPS:
        try:
            if outgoing_channel is None:
                app_module = importlib.import_module('.simple_messaging_api', package=app)

                outgoing_channel_id = app_module.send_via(outgoing_message)

                outgoing_channel = Channel.objects.filter(identifier=outgoing_channel_id).first()

                if outgoing_channel.is_enabled is False:
                    outgoing_channel = None
                else:
                    break

        except ImportError:
            pass
        except AttributeError:
            pass

    transmission_metadata = {}

    if outgoing_channel is None:
        if outgoing_message.transmission_metadata is not None:
            transmission_metadata = {}

            try:
                transmission_metadata = json.loads(outgoing_message.transmission_metadata)
            except json.decoder.JSONDecodeError:
                pass

        message_channel = transmission_metadata.get('message_channel', None)

        outgoing_channel = Channel.objects.filter(is_enabled=True, identifier=message_channel).first()

    if outgoing_channel is None:
        outgoing_channel = Channel.objects.filter(is_enabled=True, is_default=True).first()

    if outgoing_channel is None:
        outgoing_channel = Channel.objects.filter(is_enabled=True).first()

    return outgoing_channel

def process_outgoing_message(outgoing_message, metadata=None):
    outgoing_channel = channel_for_message(outgoing_message)

    channel_packages = ['simple_messaging_switchboard']

    for channel in Channel.objects.all():
        package_name = channel.channel_type.package_name

        if (package_name in channel_packages) is False:
            channel_packages.append(package_name)

    for app in settings.INSTALLED_APPS:
        if (app in channel_packages) is False:
            try:
                app_module = importlib.import_module('.simple_messaging_api', package=app)

                response = app_module.process_outgoing_message(outgoing_message, metadata=metadata)

                if response is not None:
                    return response
            except ImportError:
                pass
            except AttributeError:
                pass

    if outgoing_channel is not None:
        return outgoing_channel.send(outgoing_message, metadata=metadata)

    return None

def simple_messaging_media_enabled(outgoing_message):
    outgoing_channel = channel_for_message(outgoing_message)

    try:
        app_module = importlib.import_module('.simple_messaging_api', package=outgoing_channel.channel_type.package_name)

        return app_module.simple_messaging_media_enabled(outgoing_message)
    except ImportError:
        pass
    except AttributeError:
        pass

    return False

def process_incoming_request(request): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    for app in settings.INSTALLED_APPS:
        if app != 'simple_messaging_switchboard':
            try:
                app_module = importlib.import_module('.simple_messaging_api', package=app)

                response = app_module.process_incoming_request(request)

                if response is not None:
                    return response
            except ImportError:
                pass
            except AttributeError:
                pass

    return None

def process_incoming_message(incoming_message):
    recipient = incoming_message.recipient

    for channel in Channel.objects.filter(is_enabled=True):
        config = channel.fetch_configuration()

        phone_number = config.get('phone_number', None)

        if phone_number == recipient:
            transmission_metadata = {}

            try:
                transmission_metadata = json.loads(incoming_message.transmission_metadata)
            except json.JSONDecodeError:
                pass

            transmission_metadata['message_channel'] = channel.identifier

            incoming_message.transmission_metadata = json.dumps(transmission_metadata, indent=2)
            incoming_message.save()


def simple_messaging_fetch_active_channels(): # pylint:disable=invalid-name
    channels = []

    for channel in Channel.objects.filter(is_enabled=True).order_by('is_default', 'name'):
        channels.append([channel.identifier, channel.name])

    return channels

def annotate_console_messages(messages):
    incoming_cache = {}

    for message in messages:
        direction = message.get('direction', None)

        if direction == 'from-system':
            outgoing = OutgoingMessage.objects.filter(pk=message.get('message_id', -1)).first()

            if outgoing is not None:
                channel = channel_for_message(outgoing)

                if channel is not None:
                    message['channel'] = channel.identifier
                    message['channel_name'] = channel.name
        elif direction == 'from-user':
            incoming = IncomingMessage.objects.filter(pk=message.get('message_id', -1)).first()

            if incoming is not None:
                for channel in Channel.objects.filter(is_enabled=True):
                    config = incoming_cache.get(channel.identifier)

                    if config is None:
                        config = channel.fetch_configuration()
                        incoming_cache[channel.identifier] = config

                    if incoming.recipient == config.get('phone_number', ''):
                        message['channel'] = channel.identifier
                        message['channel_name'] = channel.name
