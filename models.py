# pylint: disable=line-too-long, no-member
import importlib
import json

from six import python_2_unicode_compatible

from django.core.checks import Warning, register # pylint: disable=redefined-builtin
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
def check_twilio_settings_defined(app_configs, **kwargs): # pylint: disable=unused-argument
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
