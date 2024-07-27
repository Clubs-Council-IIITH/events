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
