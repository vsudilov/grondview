#!/bin/bash

/bin/sed -i 's/\[self.user.email, \]/\[email for email in userena_settings.VERIFY_REQUEST_EMAILS\]/g' /usr/local/lib/python2.7/dist-packages/userena/models.py
/bin/sed -i 's/login(request, auth_user)/#login(request, author_user)/g' /usr/local/lib/python2.7/dist-packages/userena/views.py

if ! /bin/grep -q 'VERIFY_REQUEST_EMAILS' "/usr/local/lib/python2.7/dist-packages/userena/settings.py" ; then
  echo "VERIFY_REQUEST_EMAILS=settings.VERIFY_REQUEST_EMAILS" >> /usr/local/lib/python2.7/dist-packages/userena/settings.py
fi
