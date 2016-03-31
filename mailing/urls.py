# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import MirrorView


urlpatterns = [
    url(r'^mirror/(?P<signed_pk>[0-9]+:[a-zA-Z0-9_-]+)/$',
        MirrorView.as_view(), name='mirror'),
]
