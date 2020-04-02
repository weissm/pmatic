from __future__ import print_function

import sys
sys.path.append("pmatic/module_py")
import pmatic.notify
import pmatic.manager
#import pmatic.api
import pmatic

#import os

mail = pmatic.notify.Mailer(username=pmatic.manager.Config.email_username, password=pmatic.manager.Config.email_password, server="posteo.de", port=587)
mail.send(subject="test subject", to="matthias.h.weiss@gmail.com",content="content", content_type="plain")

# import smtplib
##server = smtplib.SMTP('posteo.de', 587)
#server.starttls()

#Next, log in to the server
#server.login(pmatic.manager.Config.email_username, pmatic.manager.Config.email_password)

#Send the mail
msg = " \
Hello!" # The /n separates the message from the headers
#server.sendmail("matthias.weiss@posteo.de", "matthias.h.weiss@gmail.com", msg)
#server.quit


