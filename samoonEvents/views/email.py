"""Email handling module for sending event invitations.

This module provides functionality for sending event invitation emails to guests
using Flask-Mail. It renders HTML email templates and handles the email sending
process.
"""
from flask import render_template
from flask_mail import Message
from ..app import mail


def send_invitation_email(recipient_email, event_details, invitation_id):
    """Send an event invitation email to a recipient.

    Renders an HTML email template with the provided event details and sends
    it to the specified recipient using Flask-Mail.

    Args:
        recipient_email (str): Email address of the recipient
        event_details (dict): Dictionary containing event details:
            - event_name (str): Name of the event
            - event_date (str): Date of the event
            - event_time (str): Time of the event
            - event_location (str): Location of the event
        invitation_id (int): Unique identifier for this invitation

    Returns:
        bool: True if email was sent successfully, False if an error occurred

    Raises:
        No exceptions are raised - errors are caught and logged
    """
    try:
        # Render the HTML template with event details
        html_body = render_template('invitation.html',
            event_name=event_details['event_name'],
            event_date=event_details['event_date'],
            event_time=event_details['event_time'],
            event_location=event_details['event_location'],
            invitation_id=invitation_id
        )

        msg = Message(
            subject=f"You're invited to {event_details['event_name']}!",
            recipients=[recipient_email],
            html=html_body
        )

        mail.send(msg)
        return True
    except Exception as e:
        return False
