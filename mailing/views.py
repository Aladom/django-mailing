# -*- coding: utf-8 -*-
from django.core.exceptions import SuspiciousOperation
from django.core.signing import Signer, BadSignature
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from .conf import MIRROR_SIGNING_SALT
from .models import Mail


class MirrorView(View):

    def get(self, request, *args, **kwargs):
        signed_pk = kwargs['signed_pk']
        signer = Signer(salt=MIRROR_SIGNING_SALT)
        try:
            pk = signer.unsign(signed_pk)
        except BadSignature as e:
            raise SuspiciousOperation(e)

        mail = get_object_or_404(Mail, pk=pk)

        return HttpResponse(mail.html_body)
