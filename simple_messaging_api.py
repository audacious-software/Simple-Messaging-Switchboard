# pylint: disable=line-too-long, no-member

import importlib

from django.conf import settings

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
