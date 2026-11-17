from django.http import FileResponse
from django.shortcuts import get_object_or_404

from .models import Channel

def simple_messaging_channel_vcf(request, identifier): # pylint: disable=unused-argument
    channel = get_object_or_404(Channel, identifier=identifier)

    if channel.virtual_contact_file:
        channel.virtual_contact_file.open('rb')

        response = FileResponse(channel.virtual_contact_file, content_type=' text/vcard')

        response['Content-Disposition'] = 'attachment; filename="%s.vcf"' % identifier

        return response

    return FileResponse(status=404)
