# -*- coding: utf-8 -*-

import threading

from celery import shared_task

from django.conf import settings
from django.core.mail import get_connection
from django.core.mail import EmailMessage
from django.template import loader


@shared_task
def blocking_mailto(template_name, subject, to_mail, context=None,
                    request=None, from_mail=None, cc=None):
    """
    Based on Django's send_mail, to send notify email
    Arguments:
        template = the template of mail
        to_mail = to someone's email address
        subject = define the subject of the mail
        context = Context to render the mail content
    """
    try:
        t = loader.get_template(template_name)
        if request:
            mail_content = t.render(context=context, request=request)
        else:
            mail_content = t.render(context=context)

        connection = get_connection(username=None,
                                    password=None,
                                    fail_silently=False)

        subject = settings.EMAIL_SUBJECT_PREFIX + subject
        from_email = from_mail or settings.EMAIL_FROM
        recipient_list = isinstance(to_mail, list) \
            and list(set(to_mail)) or [to_mail, ]
        EmailMessage(subject, mail_content, from_email, recipient_list,
                     connection=connection, bcc=cc).send()
    except Exception:
        if settings.DEBUG:
            raise


def non_blocking_mailto(template_name, subject, recipients=None,
                        context=None, sender=settings.EMAIL_FROM,
                        cc=None):
    t = loader.get_template(template_name)
    body = t.render(context)
    if settings.DEBUG:
        recipients = settings.EMAILS_FOR_DEBUG

    email_msg = EmailMessage(subject=subject, body=body,
                             from_email=sender, to=recipients, bcc=cc)

    email_thread = threading.Thread(target=email_msg.send, args=[True, ])
    # This is to tell Python not to wait for the thread to return
    email_thread.setDaemon(True)
    email_thread.start()


if settings.ENABLE_ASYNC_EMAIL:
    send_email_using_threading = mailto = blocking_mailto.delay
else:
    send_email_using_threading = non_blocking_mailto
    mailto = blocking_mailto
