# pylint: disable=line-too-long, no-member
import importlib
import json
import os

import requests

from six import python_2_unicode_compatible

from django.conf import settings
from django.core.checks import Error, Warning, register # pylint: disable=redefined-builtin
from django.db import models
from django.db.utils import ProgrammingError


@python_2_unicode_compatible
class ChannelType(models.Model):
    name = models.CharField(max_length=1024, unique=True)
    package_name = models.CharField(max_length=1024, unique=True)

    def __str__(self): # pylint: disable=invalid-str-returned
        return '%s (%s)' % (self.name, self.package_name)

@python_2_unicode_compatible
class Channel(models.Model):
    name = models.CharField(max_length=1024, unique=True)
    identifier = models.SlugField(max_length=1024, unique=True)

    channel_type = models.ForeignKey(ChannelType, on_delete=models.CASCADE)

    is_enabled = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    configuration = models.TextField(default='{}')

    virtual_contact_file = models.FileField(upload_to='simple_messaging_vcf_files', null=True, blank=True)

    def fetch_configuration(self):
        return json.loads(self.configuration)

    def is_valid(self):
        return self.fetch_configuration() is not None

    def __str__(self): # pylint: disable=invalid-str-returned
        return '%s (%s)' % (self.name, self.identifier)

    def send(self, outgoing_message, metadata=None):
        if metadata is None:
            metadata = {}

        app_module = importlib.import_module('.simple_messaging_api', package=self.channel_type.package_name)

        channel_config = self.fetch_configuration()

        metadata.update(channel_config)

        prefix = channel_config.get('prefix', None)

        if prefix is not None:
            destination = outgoing_message.current_destination()

            if destination.startswith(prefix) is False:
                dest_tokens = destination.split(':')

                metadata['destination'] = '%s:%s' % (prefix, dest_tokens[-1])

        return app_module.process_outgoing_message(outgoing_message, metadata=metadata)

@register()
def check_channel_type_defined(app_configs, **kwargs): # pylint: disable=unused-argument
    errors = []

    try:
        if ChannelType.objects.all().count() == 0:
            error = Warning('No ChannelType objects defined.', hint='Add a ChannelType object with corresponding messaging channel type.', obj=None, id='simple_messaging_switchboard.E001')
            errors.append(error)

        if Channel.objects.all().count() == 0:
            error = Warning('No Channel objects defined.', hint='Add a new messaging channel.', obj=None, id='simple_messaging_switchboard.E002')
            errors.append(error)
    except ProgrammingError:
        pass # Migrations not applied

    return errors

@register()
def check_channel_package(app_configs, **kwargs): # pylint: disable=unused-argument
    errors = []

    try:
        for channel in ChannelType.objects.all():
            if (channel.package_name in settings.INSTALLED_APPS) is False:
                error = Error('"%s" set as a channel type, but is not present in settings.INSTALLED_APP' % channel.package_name, hint='Add "%s" to INSTALLED_APPS.' % channel.package_name, obj=None, id='simple_messaging_switchboard.E003')

                errors.append(error)
    except ProgrammingError:
        pass # Migrations not applied

    return errors

@register()
def check_channel_prefixes(app_configs, **kwargs): # pylint: disable=unused-argument
    errors = []

    try:
        for channel in Channel.objects.all():
            config = channel.fetch_configuration()

            phone_number = config.get('phone_number', '')

            tokens = phone_number.split(':')

            if len(tokens) > 1:
                expected_prefix = tokens[0]

                prefix = config.get('prefix', None)

                if prefix is None or prefix != expected_prefix:
                    error = Warning('Channel "%s" with phone number defined with "%s" prefix, but no "prefix" option included with channel configuration.' % (channel, expected_prefix), hint='Add "prefix": "%s" to channel configuration.' % expected_prefix, obj=None, id='simple_messaging_switchboard.W001')
                    errors.append(error)
    except ProgrammingError:
        pass # Migrations not applied

    return errors

@register()
def check_channel_phone_numbers(app_configs, **kwargs): # pylint: disable=unused-argument
    errors = []

    try:
        for channel in Channel.objects.all():
            config = channel.fetch_configuration()

            phone_number = config.get('phone_number', None)

            if phone_number is None:
                error = Warning('Channel "%s" has no defined "phone_number" parameter.' % channel, hint='Add "phone_number" to channel configuration, even if this is a loopback channel.', obj=None, id='simple_messaging_switchboard.W002')
                errors.append(error)
    except ProgrammingError:
        pass # Migrations not applied

    return errors

@register()
def check_install_order(app_configs, **kwargs): # pylint: disable=unused-argument
    errors = []

    switchboard_seen = False

    try: # pylint: disable=too-many-nested-blocks
        for app in settings.INSTALLED_APPS:
            if app == 'simple_messaging_switchboard':
                switchboard_seen = True
            else:
                try:
                    simple_messaging_api = importlib.import_module('.simple_messaging_api', package=app)

                    if switchboard_seen is False:
                        if hasattr(simple_messaging_api, 'process_incoming_message'):
                            error = Warning('Django app "%s" included before simple_messaging_switchboard. ' % app, hint='Verify order of settings.INSTALLED_APPS.', obj=None, id='simple_messaging_switchboard.W003')
                            errors.append(error)
                except: # nosec # pylint: disable=bare-except
                    pass

    except ProgrammingError:
        pass # Migrations not applied

    return errors

@register()
def check_media_upload_protected(app_configs, **kwargs): # pylint: disable=unused-argument
    errors = []

    if 'simple_messaging_switchboard.W002' in settings.SILENCED_SYSTEM_CHECKS or 'simple_messaging_switchboard.E002' in settings.SILENCED_SYSTEM_CHECKS:
        return errors

    http_url = 'https://%s%ssimple_messaging_vcf_files' % (settings.ALLOWED_HOSTS[0], settings.MEDIA_URL,)

    try:
        response = requests.get(http_url, timeout=300)

        if (200 <= response.status_code < 400) and len(response.text) > 0: # pylint: disable=len-as-condition
            error = Error('Incoming media folder is readable over HTTP', hint='Update webserver configuration to deny read access (' + http_url + ') via HTTP(S).', obj=None, id='simple_messaging_switchboard.E002')

            errors.append(error)
    except: # pylint: disable=bare-except
        warning = Warning('Unable to connect to %s' % http_url, hint='Verify that the webserver is properly configured.', obj=None, id='simple_messaging_switchboard.W002') # pylint: disable=consider-using-f-string

        errors.append(warning)

    return errors

@register()
def check_media_upload_available(app_configs, **kwargs): # pylint: disable=unused-argument
    errors = []

    folder_path = os.path.join(settings.MEDIA_ROOT, 'simple_messaging_vcf_files')

    if os.path.exists(folder_path) is False:
        error = Error('Raw VCF folder is missing', hint='Verify that the folder for media files (' + folder_path + ') is present on the local filesystem.', obj=None, id='simple_messaging_switchboard.E003')

        errors.append(error)

    return errors
