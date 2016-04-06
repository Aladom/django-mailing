Get started
===========

Queue e-mails
-------------

This is quite an unusual start, however will we start by queuing an e-mail.
Even though no campaign exist for now, this is usually where you will start.

Say you are implementing user registration and want to send an e-mail to
welcome him and give him a temporary password. This would give something like
this:

.. highlight:: python

   from django.contrib.auth import get_user_model

   from mailing.utils import queue_mail

   User = get_user_model()
   password = User.objects.make_random_password()
   user = User.objects.create_user(..., password=password)

   queue_mail('user_registration', {
       'user': user,
       'password': password,
   })

``queue_mail()`` will look for a campaign with the key ``user_registration``
and create a mail instance with the template of this campaign and the context
you passed as second argument. The mail instance will then be stored in the
database with the state "pending", which means ready to be sent.

For now, no campaign exist with the key "user_registration". In such case, a
python warning will be emitted (that you should see in your logs) and no mail
will be queued. You can override this behavior to raise a
``Campaign.DoesNotExist`` exception instead of emitting a warning.


Create a Campaign
-----------------

Let's create a campaign. Go to
http://127.0.0.1:8000/admin/mailing/campaign/ and click
"Add e-mail campaign" button to access the campaign creation form.

You will be asked for:

Key
  This must be unique. It will be used to reference this campaign in your
  python code. Basically, when you want to queue an e-mail.

  Example: user_registration

Name
  Provide a name for this campaign. Uniqueness is not enforced, though you will
  likely want to choose a unique name for each campaign.

  Example: User registration

E-mail subject
  The subject of e-mails that will be created from this campaign. It may
  contain template variable and django built-in template tags that will be
  evaluated to render the subject.

  Example: Welcome {{ user.first_name }}

Template file
  You may use this file field to attach a template for the HTML body of e-mails
  created from this campaign. However it is better to leave it blank and create
  your file ``mailing/user_registration.html`` (where ``user_registration`` is
  the campaign key defined above) in one of your templates directories.

Extra headers
  Lets you define e-mail headers. The most important header "To". You will very
  likely want to define it for every campaign. Though it is possible to pass it
  at e-mail cretaion, in most case you can define it at campaign level since
  template variable are accepted. For instance, you can set the "To" header to
  ``{{ user.get_full_name }} <{{ user.email }}>``. You may also want to set the
  "From" header, but it is often not needed as ``DEFAULT_FROM_EMAIL`` will be
  used as default.

.. note:: Some fields are not described above. These are not important for
   basic use and will be described later.

Write your mail template
------------------------

Now create a folder "mailing" in one of your templates directories and create
a file "user_registration.html" (or whatever campaign key you chose dot html)
in this folder. Write your e-mail template as you would write any other
template.

.. highlight:: html

   {% extends "mailing/base_layout.html" %}
   {% load i18n %}
   {% block content %}
     <h1>{% trans "Welcome on board" %}</h1>
     <p>{% blocktrans with name=user.first_name %}Hi {{ name }}, we are very
     happy to count you among our members.{% endblocktrans %}</p>
     <p>{% trans "Here are your credentials:" %}</p>
     <ul>
       <li><b>{% trans "Username:" %}</b> {{ user.username }}</li>
       <li><b>{% trans "Password:" %}</b> {{ password }}</li>
     </ul>
     <p>{% blocktrans %}We strongly encourage you to change your password as
     you first log in.{% endblock %}</p>
   {% endblock %}


Of course, it's up to you to define "mailing/base_layout.html" or not extend
any layout at all. The use of i18n template tags library is also here only as
an example.
