import requests
from string import Template

# email templates
PROGRESS_EVENT_SUBJECT = Template(
    """ 
[Events] Approval request from $club
"""
)

PROGRESS_EVENT_BODY = Template(
    """
$club is requesting you to review and approve their event, $event.

To view more details and approve or reject the event, visit the link below:
$eventlink



This is an automated email sent on behalf of $uid. Please do not reply to this email.
"""
)


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
            mutation Mutation($mailInput: MailInput!) {
              sendMail(mailInput: $mailInput)
            }
        """
        variables = {
            "mailInput": {
                "body": body,
                "subject": subject,
                "uid": uid,
                "toRecipients": toRecipients,
                "ccRecipients": ccRecipients,
            }
        }
        if cookies:
            requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variables},
                cookies=cookies,
            )
        else:
            requests.post(
                "http://gateway/graphql", json={"query": query, "variables": variables}
            )

    except:
        return None
