from string import Template

# Email Templates

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


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)

PROGRESS_EVENT_BODY_FOR_SLO = Template(
    """
Dear Sir/Ma'am,

We are writing to request a venue & approval for an event organized by $club. Please find the event details provided by the club below.

     1. Event ID: $event_id

     2. Purpose: $event

     3. Event Description: $description

     4. Expected Number of Students: $student_count

     5. Start Date: $start_time
     6. End Date  : $end_time

     7. Location  : $location

     8. Budget    : $budget

     9. Equipment Support      : $equipment
    10. Additional Information : $additional

    11. Point of Contact -
        Name   : $poc_name
        RollNo : $poc_roll
        Email  : $poc_email
        Phone  : $poc_phone

Should you require any further information or clarification, please do not hesitate to reach out to us.

Best regards,
Clubs Council.


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)

PROGRESS_EVENT_BODY_FOR_SLC = Template(
    """
Dear Sir/Ma'am,

We are writing to request for your approval for an event organized by $club. Please find the event details provided by the club below.

    1. Event ID: $event_id
    2. Title: $event

    3. Event Description: $description

    4. Date & Time: $start_time to $end_time
    5. Expected Number of Students: $student_count

    6. Location  : $location

    7. Budget    : $budget

    8. Additional Information : $additional

    9. Approval/Event Link: $eventlink

Should you require any further information or clarification, please do not hesitate to reach out to us.

Best regards,
Clubs Council.


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)

DELETE_EVENT_SUBJECT = Template(
    """
[Events] $event_id: Deletion of $event
"""
)

DELETE_EVENT_BODY_FOR_CC = Template(
    """
Dear Clubs Council,

$club has deleted the event, $event.

To view more details, visit the link below:
$eventlink


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)

# Email Templates For Clubs

CLUB_EVENT_SUBJECT = Template(
    """
[Events] $event_id: $event Request Receipt
"""
)

SUBMIT_EVENT_BODY_FOR_CLUB = Template(
    """
Dear $club,

This is to confirm that we have received your request for $event. 

Please be informed that your request is currently under review by our executive team. Once we have completed our internal review process, your request will be forwarded to the Student Life Committee for final review and approval.

    1. Event ID: $event_id

    2. Purpose: $event

    3. Event Description: $description

    4. Start Date: $start_time
    5. End Date  : $end_time

    6. Location  : $location

    7. Budget    : $budget

    8. Point of Contact -
        Name   : $poc_name
        RollNo : $poc_roll
        Email  : $poc_email
        Phone  : $poc_phone
    
    9. Event Link: $eventlink

Should you have any queries or require assistance at any stage of the process, please do not hesitate to reach out to us. We are here to ensure a smooth and efficient coordination of your event.
    
Best regards,
Clubs Council.


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)

APPROVED_EVENT_BODY_FOR_CLUB = Template(
    """
Dear $club,

Your event, $event, has been approved.

To view more details, visit the link below:
$eventlink


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)

DELETE_EVENT_BODY_FOR_CLUB = Template(
    """
Dear $club,

Your event, $event, has been deleted from the system, from the side of $deleted_by.

To view more details, visit the link below:
$eventlink


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)

EVENT_BILL_STATUS_SUBJECT = Template(
    """
Update on Bill Status for $event
"""
)

EVENT_BILL_STATUS_BODY_FOR_CLUB = Template(
    """
Dear Club,

SLO have updated the status for the bills for the event, $event

Updated Status: $bill_status
Comment: $comment
Event Link: $eventlink

Should you have any queries or require assistance at any stage of the process, please do not hesitate to reach out to us. We are here to ensure a smooth and efficient coordination of your event.

Best regards,
Clubs Council.


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)

REJECT_EVENT_SUBJECT = Template(
    """
[Events] $event_id: Rejection of $event
"""
)

REJECT_EVENT_BODY_FOR_CLUB = Template(
    """
Dear $club,

Your event, $event, has been rejected from the system, from the side of
$deleted_by has been sent back for edits.

The Reason Specified is:
$reason

To edit the details, visit the link below:
$eventlink

Best regards,
Clubs Council.


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)



