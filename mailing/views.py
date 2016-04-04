# -*- coding: utf-8 -*-
from django.contrib import messages
from django.core.exceptions import SuspiciousOperation
from django.core.signing import Signer, BadSignature
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View, FormView

from .conf import MIRROR_SIGNING_SALT, SUBSCRIPTION_SIGNING_SALT
from .forms import SubscriptionsManagementForm
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


class SubscriptionsManagementView(FormView):

    template_name = 'mailing/subscriptions/management.html'
    form_class = SubscriptionsManagementForm

    def dispatch(self, request, *args, **kwargs):
        signed_email = kwargs['signed_email']
        signer = Signer(salt=SUBSCRIPTION_SIGNING_SALT)
        try:
            self.email = signer.unsign(signed_email)
        except BadSignature as e:
            raise SuspiciousOperation(e)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['email'] = self.email
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _(
            "E-mail subscriptions saved successfully."
        ))
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.path
