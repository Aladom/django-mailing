# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import MirrorView, SubscriptionsManagementView


urlpatterns = [
    url(r'^mirror/(?P<signed_pk>[0-9]+:[a-zA-Z0-9_-]+)/$',
        MirrorView.as_view(), name='mirror'),
    url(r'^subscriptions/(?P<signed_email>.+:[a-zA-Z0-9_-]+)/$',
        SubscriptionsManagementView.as_view(), name='subscriptions'),
]
