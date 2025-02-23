#import logging
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#logger = logging.getLogger(__name__)

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

        #logger.info(f"mailbody: {body}")
        # logging.info(requests.post(
        #     "http://gateway/graphql",
        #     json={"query": query, "variables": variables},
        # ).text)

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
