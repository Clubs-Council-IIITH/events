import os

import requests

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
        """
        variables = {
            "mailInput": {
                "body": body,
                "subject": subject,
                "uid": uid,
                "toRecipients": toRecipients,
                "ccRecipients": ccRecipients,
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
