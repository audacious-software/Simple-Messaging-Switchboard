# pylint: disable=line-too-long
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.conf import settings
from django.contrib import admin
from django.utils import timezone

from .models import ChannelType, Channel

@admin.register(ChannelType)
class ChannelTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'package_name',)

    search_fields = ('name', 'package_name',)

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'identifier', 'channel_type', 'is_default', 'is_enabled', 'is_valid')
    list_filter = ('is_default', 'is_enabled', 'channel_type',)

    search_fields = ('name', 'identifier', 'configuration')
