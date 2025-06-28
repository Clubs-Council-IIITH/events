"""
Contains templates for emails to be sent to CC, SLO, SLC and the club
regarding the event's approval and its status to interested parties.
"""

from string import Template

# Email Templates

# email template requesting approval for an event to
# CC(Clubs Council),SLO(Student Life Office) and SLC(Student Life Committee).
# common subject but 3 different bodies
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
     8. Alternate Location  : $locationAlternate

     9. Budget    : $budget
    10. Sponsored Amount   : $sponsor

    11. Equipment Support      : $equipment
    12. Additional Information : $additional

    13. Point of Contact -
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
    7. Alternate Location  : $locationAlternate

    8. Budget    : $budget
    9. Sponsored Amount   : $sponsor

    10. Additional Information : $additional

    11. Approval/Event Link: $eventlink

Should you require any further information or clarification, please do not hesitate to reach out to us.

Best regards,
Clubs Council.


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)

# email template informing the deletion of the event from the club's side
# and informing the CC(Clubs Council).
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

# email template informing the club regarding the status of the events
# approval.
# regarding processing, approval and rejection status of the event even
# if the event was deleted by the CC.
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
    7. Alternate Location  : $locationAlternate

    8. Budget    : $budget

    9. Sponsored Amount   : $sponsor

    10. Point of Contact -
        Name   : $poc_name
        RollNo : $poc_roll
        Email  : $poc_email
        Phone  : $poc_phone
    
    11. Event Link: $eventlink

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

# email template informing the club regarding the status of the event's
# budget by SLO.
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

# email template informing the club regarding the rejection of the event.
REJECT_EVENT_SUBJECT = Template(
    """
[Events] $event_id: $event Rejected
"""
)

REJECT_EVENT_BODY_FOR_CLUB = Template(
    """
Dear $club,

Your event, $event, has been sent back for revisions by $deleted_by.

Reason Provided:
$reason

To update the event details, please visit the following link:
$eventlink

Best regards,
Clubs Council.


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)


# email template for reminding clubs to submit event reports or budget updates
EVENT_REPORT_REMINDER_SUBJECT = Template(
    """
[Events] $event_id: Reminder to Submit Report for $event
"""
)

EVENT_REPORT_REMINDER_BODY = Template(
    """
Dear $club,

This is a reminder to submit the event report or budget update for your event, $event.

Please ensure that the report is submitted by the specified deadline. Failure to submit the report on time may result in delays in processing future event requests or budget approvals.

To submit the report or update the budget details, visit the link below:
$eventlink

Should you have any queries or require assistance at any stage of the process, please do not hesitate to reach out to us. We are here to ensure a smooth and efficient coordination of your event.

Best regards,
Clubs Council.


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)


# email template for reminding clubs about pending bills or payment updates
EVENT_BILL_REMINDER_SUBJECT = Template(
    """
[Events] $event_id: Reminder to Submit Bill Details for $event
"""
)

EVENT_BILL_REMINDER_BODY = Template(
    """
Dear $club,

This is a reminder to submit the bill details or payment updates for your event, $event.

Please ensure that the bill details are submitted by the specified deadline. Failure to submit the bill details on time may result in delays in processing reimbursements or future event approvals.

Your event had a budget of $total_budget INR. All bills must be submitted for processing reimbursements/settling advance.

To submit the bill details or update payment information, visit the link below:
$eventlink

Should you have any queries or require assistance at any stage of the process, please do not hesitate to reach out to us. We are here to ensure a smooth and efficient coordination of your event.

Best regards,
Clubs Council.


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)

REMIND_SLO_APPROVAL_SUBJECT = Template(
    """
[Reminder] Pending Approval for Event: $event
"""
)

REMIND_SLO_APPROVAL_BODY = Template(
    """
Dear SLO,

This is a reminder to review and approve the event "$event" submitted by $club.

Event ID: $event_id  
Date & Time: $start_time to $end_time  
Location: $location  

Please approve or reject the event at the following link:  
$eventlink  

Best regards,  
Clubs Council  

(Note: This is an automated reminder from the Clubs Council system.)
"""  # noqa: E501
)


# email template for informing SLO when a club submits bills for an event
BILL_SUBMISSION_SUBJECT = Template(
    """
[Events] $event_id: Bill Submitted for $event
"""
)

BILL_SUBMISSION_BODY_FOR_SLO = Template(
    """
Dear SLO,

This is to inform you that $club has submitted bill(s) for their event, $event.

Event Details:
    1. Event ID: $event_id
    2. Event Name: $event
    3. Event Date: $event_date
    4. Total Proposed Budget: $total_budget
    5. Total Budget Used: $total_budget_used

To review the bills and update their status, please visit:
$eventfinancelink

Should you have any questions or require additional information, please don't hesitate to reach out to the club or Clubs Council.

Best regards,
Clubs Council.


Note: This automated email has been generated from the Clubs Council website. For more details, visit clubs.iiit.ac.in.
"""  # noqa: E501
)
