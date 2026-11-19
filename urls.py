# pylint: disable=line-too-long, wrong-import-position

import sys

if sys.version_info[0] > 2:
    from django.urls import re_path as url # pylint: disable=no-name-in-module
else:
    from django.conf.urls import url

from .views import simple_messaging_channel_vcf

urlpatterns = [
    url(r'^(?P<identifier>.+).vcf', simple_messaging_channel_vcf, name='simple_messaging_channel_vcf'),
]
