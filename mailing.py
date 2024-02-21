import requests
from string import Template

# email templates
PROGRESS_EVENT_SUBJECT = Template(
    """
[Events] Approval request for $event
"""
)

PROGRESS_EVENT_BODY = Template(
    """
$club is requesting you to review and approve their event, $event.

To view more details and approve or reject the event, visit the link below:
$eventlink



This is an automated email sent from the Clubs Council Website. Please do not reply to this email.
"""
)

PROGRESS_EVENT_BODY_FOR_SLO = Template(
    """
Respected sir,

$club needs a room for their event, so kindly requesting you to proceed with the room booking request.

    1. Purpose: $event
    2. Description by Club: $description
    3. Expected number of students: $student_count
    4. Date and Day: $date
    5. Start Time: $start_Time
    6. End Time: $end_Time
    7. Location: $room_no
    8. POC -
        Name: $poc_name
        Rollno: $poc_roll
        Email: $poc_email
        Phone: $poc_phone

Best Regards,
Clubs Council.

This is an automated email sent from the Clubs Council Website. Please do not reply to this email.
"""
)

APPROVED_EVENT_SUBJECT = Template(
    """
[Events] Your event, $event, has been approved!
"""
)

APPROVED_EVENT_BODY = Template(
    """
Your event, $event, has been approved.

To view more details, visit the link below:
$eventlink


This is an automated email sent from the Clubs Council Website. Please do not reply to this email.
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

    except Exception:
        return None
