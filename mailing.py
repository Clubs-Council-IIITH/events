import os

import requests

from utils import convert_to_html

inter_communication_secret = os.getenv("INTER_COMMUNICATION_SECRET")


# API call to send mail notification
def triggerMail(
    uid,
    subject,
    body,
    toRecipients,
    ccRecipients=[],
    cookies=None,
) -> None:
    """
    Method to trigger an email

    This method is used to trigger an email.
    It makes a mutation request which is resolver by the sendMail resolver from mailing.py from interfaces.py.
    It send an email with the given parameters.

    Args:
        uid : The user id.
        subject : The subject of the email.
        body : The body of the email.
        to : The list of to recipients.
        cc : The list of cc recipients.
        cookies : The cookies.

    Returns:
        None
    """

    try:
        query = """
            mutation Mutation($mailInput: MailInput!, $interCommunicationSecret: String) {
                sendMail(mailInput: $mailInput, interCommunicationSecret: $interCommunicationSecret)
            }
        """  # noqa: E501
        variables = {
            "mailInput": {
                "body": convert_to_html(body),
                "subject": subject,
                "uid": uid,
                "toRecipients": toRecipients,
                "ccRecipients": ccRecipients,
                "htmlBody": True,
            },
            "interCommunicationSecret": inter_communication_secret,
        }
        if cookies:
            requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variables},
                cookies=cookies,
            )
        else:
            requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variables},
            )

    except Exception:
        return None
