Get started
===========

Create a Campaign
-----------------

First let's create a campaign. Go to
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
