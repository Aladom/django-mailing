.. Django Mailing Campaign documentation master file, created by
   sphinx-quickstart on Tue Apr  5 14:38:23 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Django Mailing Campaign's documentation!
===================================================

Django Mailing Campaign is a Django_ application to manage your e-mails. It
was developed by Aladom_ and Cocoonr_ companies for their own needs and is
distributed under MIT license in the hope it will be useful to other
developers.

Features
--------

Campaigns
  Create campaigns for each type of e-mail, setup a template and default
  headers. Then create e-mails by passing a campaign identifier and context
  data to render the body, the subject and headers.

E-mails queuing
  Rather than sending e-mails directly, you can queue them in your database
  and run a script in background to send queued e-mails.

Delay e-mails sending
  Set the date and time when a mail should be sent.

Mirror pages
  Provide an online version of your e-mails in case the recipients face
  difficulties to read your e-mails in their mailbox.

Manage subscriptions
  Define different e-mail types and let your recipients choose which kind of
  e-mails they wish to receive and unsubscribe from undesired e-mails.

Attachments
  Add attachments to your e-mails and campaigns.

Plain text and HTML support
  While you will likely want to write HTML messages, it is important to
  provide a fallback plain text message. Django Mailing Campaign handles this
  and automatically create an plain text version of your e-mails.

.. _Django: https://www.djangoproject.com/
.. _Aladom: http://www.aladom.fr/
.. _Cocoonr: https://cocoonr.fr/

Contents:

.. toctree::
   :maxdepth: 2
   :caption: Features



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

