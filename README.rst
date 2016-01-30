==============
Django Mailing
==============

Mailing app for django

Quick start
-----------

1. Add "mailing" to your INSTALLED_APPS setting like this::

   INSTALLED_APPS = [
       ...
       'mailing',
   ]

2. Run `python manage.py migrate` to create the mailing models

3. Start the development server and visit http://127.0.0.1:8000/admin/
   to manage e-mails (you'll ne the Admin app enabled).
