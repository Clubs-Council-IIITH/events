import os
from typing import List

from httpx import AsyncClient

from utils import convert_to_html

inter_communication_secret = os.getenv("INTER_COMMUNICATION_SECRET")


# API call to send mail notification
async def triggerMail(
    uid: str,
    subject: str,
    body: str,
    cookies: dict | None = None,
    toRecipients: List[str] = [],
    ccRecipients: List[str] = [],
) -> None:
    """
    Method triggers a mutation request, resolved by the sendMail resolver from
    mailing.py from interfaces microservice, it triggers a email.

    Args:
        uid (str): The user id.
        subject (str): The subject of the email.
        body (str): The body of the email.
        toRecipients (List[str]): The list of to recipients.
        ccRecipients (List[str]): The list of cc recipients.
        cookies (dict): The cookies. Defaults to None.
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

        # print("mailbody:", body)

        if cookies:
            async with AsyncClient(cookies=cookies) as client:
                await client.post(
                    "http://gateway/graphql",
                    json={"query": query, "variables": variables},
                )
        else:
            raise Exception(
                "Couldn't find cookie, cannot send email without cookies!"
            )

    except Exception:
        return None
