# pylint: disable=line-too-long, no-member
import importlib
import json

from six import python_2_unicode_compatible

from django.db import models

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

        metadata.update(self.fetch_configuration())

        return app_module.process_outgoing_message(outgoing_message, metadata=metadata)
