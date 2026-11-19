# -*- coding: utf-8 -*-
# pylint: disable=no-member,line-too-long

import importlib

from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Initializes the Simple Messaging Switchboard and its dfefault channels.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        for app in settings.INSTALLED_APPS:
            try:
                app_module = importlib.import_module('.simple_messaging_api', package=app)

                app_module.create_initial_switchboard_channels()
            except ImportError:
                pass
            except AttributeError:
                pass
