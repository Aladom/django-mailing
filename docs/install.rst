Install django-mailing-campaign
===============================

Install ``django-mailing-campaign`` with pip::

    pip install django-mailing-campaign


Add ``mailing`` app to django ``INSTALLED_APPS`` in your settings.py::

    INSTALLED_APPS = [
        ...,
        'mailing',
        ...,
    ]


Optionally, if you want to use mirror pages and the subscriptions management
page, add this line to your ``urlpatterns`` in your urls.py::

    url(r'^mailing/', include('mailing.urls', namespace='mailing')),


Run your development server, visit http://127.0.0.1:8000/admin/mailing/ and
start creating campaigns.
