"""Guest management module.

This module handles all guest-related operations including:
- Adding, updating, and removing guests from events
- Sending invitations to individual and groups of guests
- Tracking invitation responses and guest attendance status
"""

from flask import jsonify, request, render_template, current_app
from flask_login import login_required, current_user
from ..models import db
from ..models.guest import Guest
from ..models.invitation import Invitation
from ..models.event import Event
from ..extensions import mail
from flask_mail import Message
from ..views import app_views
from ..views.email import send_invitation_email
import threading


@app_views.route('/event/<int:event_id>/guests', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def handle_guests(event_id):
    """Handle CRUD operations for event guests.

    Args:
        event_id (int): ID of the event to manage guests for

    Returns:
        JSON response with operation result and data

    Methods:
        GET: Retrieve all guests for an event
        POST: Add a new guest and create their invitation
        PUT: Update an existing guest's information
        DELETE: Remove a guest and their invitation
    """
    try:
        # Verify event ownership
        event = Event.query.get_or_404(event_id)
        if event.owner_id != current_user.user_id:
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403

        if request.method == 'GET':
            guests = Guest.query.filter_by(event_id=event_id).all()
            return jsonify({
                'success': True,
                'guests': [guest.serialize() for guest in guests]
            })

        elif request.method == 'POST':
            data = request.get_json()
            new_guest = Guest(
                name=data['name'],
                email=data['email'],
                phone=data.get('phone'),
                event_id=event_id,
                status='Pending'
            )

            db.session.add(new_guest)
            db.session.commit()

            # Create invitation
            invitation = Invitation(
                guest_id=new_guest.guest_id,
                event_id=event_id,
                status='Pending'
            )
            db.session.add(invitation)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Guest added successfully',
                'guest': new_guest.serialize()
            }), 201

        elif request.method == 'PUT':
            data = request.get_json()
            guest_id = data.get('guest_id')
            if not guest_id:
                return jsonify({'success': False, 'error': 'Guest ID is required'}), 400

            guest = Guest.query.get_or_404(guest_id)

            if guest.event_id != event_id:
                return jsonify({'success': False, 'error': 'Guest not found in this event'}), 404

            # Update guest information
            guest.name = data.get('name', guest.name)
            guest.email = data.get('email', guest.email)
            guest.phone = data.get('phone', guest.phone)

            try:
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'Guest updated successfully',
                    'guest': guest.serialize()
                })
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500

        elif request.method == 'DELETE':
            data = request.get_json()
            guest = Guest.query.get_or_404(data['guest_id'])

            if guest.event_id != event_id:
                return jsonify({'success': False, 'error': 'Guest not found in this event'}), 404

            # Delete associated invitations first
            Invitation.query.filter_by(guest_id=guest.guest_id).delete()

            db.session.delete(guest)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Guest deleted successfully'
            })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app_views.route('/event/<int:event_id>/guests/<int:guest_id>/invite', methods=['POST'])
@login_required
def invite_guest(event_id, guest_id):
    """Send an invitation email to a specific guest.

    Args:
        event_id (int): ID of the event
        guest_id (int): ID of the guest to invite

    Returns:
        JSON response indicating success/failure of sending invitation
    """
    try:
        # Verify event ownership
        event = Event.query.get_or_404(event_id)
        if event.owner_id != current_user.user_id:
            return jsonify({'error': 'Unauthorized access'}), 403

        guest = Guest.query.get_or_404(guest_id)

        # Create or get invitation
        invitation = Invitation.query.filter_by(
            event_id=event_id,
            guest_id=guest_id
        ).first()

        if not invitation:
            invitation = Invitation(
                event_id=event_id,
                guest_id=guest_id,
                status='Pending'
            )
            db.session.add(invitation)
            db.session.flush()

        # Send invitation email
        msg = Message(
            f"Invitation to {event.name}",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[guest.email]
        )

        msg.html = render_template(
            'invitation.html',
            event_name=event.name,
            event_date=event.date.strftime('%B %d, %Y') if event.date else 'TBD',
            event_location=event.location,
            event_description=event.description if event.description else '',
            invitation_id=invitation.invitation_id,
            invitation_status=invitation.status,
            owner_name=event.owner.username
        )

        mail.send(msg)

        # Update guest status to 'Invited'
        guest.status = 'Invited'
        invitation.status = 'Sent'
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Invitation sent successfully',
            'invitation': invitation.serialize()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@app_views.route('/event/<int:event_id>/send-all-invitations', methods=['POST'])
@login_required
def send_bulk_invitations(event_id):
    """Send invitation emails to all pending guests for an event.

    Args:
        event_id (int): ID of the event to send invitations for

    Returns:
        JSON response with counts of successful/failed invitation sends
    """
    try:
        # Verify event ownership
        event = Event.query.get_or_404(event_id)
        if event.owner_id != current_user.user_id:
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403

        pending_guests = Guest.query.filter_by(
            event_id=event_id,
            status='Pending'
        ).all()

        success_count = 0
        failed_count = 0

        for guest in pending_guests:
            try:
                # Send invitation directly instead of calling another route
                msg = Message(
                    f"Invitation to {event.name}",
                    sender=current_app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[guest.email]
                )

                # Create or get invitation
                invitation = Invitation.query.filter_by(
                    event_id=event_id,
                    guest_id=guest.guest_id
                ).first()

                if not invitation:
                    invitation = Invitation(
                        event_id=event_id,
                        guest_id=guest.guest_id,
                        status='pending'
                    )
                    db.session.add(invitation)

                msg.html = render_template(
                    'invitation.html',
                    event=event,
                    guest=guest,
                    invitation=invitation
                )

                mail.send(msg)
                guest.status = 'Invited'
                success_count += 1

            except Exception as e:
                current_app.logger.error(f"Failed to send invitation to {guest.email}: {str(e)}")
                failed_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Sent {success_count} invitations successfully. {failed_count} failed.'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app_views.route('/invitation/<int:invitation_id>/status/<status>')
def update_invitation_status(invitation_id, status):
    """Update a guest's invitation response status.

    Args:
        invitation_id (int): ID of the invitation to update
        status (str): New status ('Accepted' or 'Declined')

    Returns:
        Rendered template showing the response confirmation
    """
    try:
        # Validate status
        if status not in ['Accepted', 'Declined']:
            return render_template('invitation_response.html',
                                error="Invalid response status"), 400

        # Get invitation
        invitation = Invitation.query.get_or_404(invitation_id)

        # Update invitation status
        invitation.status = status

        # Update guest status
        guest = Guest.query.get(invitation.guest_id)
        if status == 'Accepted':
            guest.status = 'Attending'
        elif status == 'Declined':
            guest.status = 'Not Attending'

        # Get event name for the response template
        event = Event.query.get(invitation.event_id)

        db.session.commit()

        # Redirect to response page
        return render_template('invitation_response.html',
                             status=status,
                             event_name=event.name)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating invitation status: {str(e)}")
        return render_template('invitation_response.html',
                             error="An error occurred processing your response"), 500


@app_views.route('/send-invitation/<event_id>/<email>')
def send_event_invitation(event_id, email):
    """Send an invitation email for an event.

    Args:
        event_id (int): ID of the event
        email (str): Email address to send invitation to

    Returns:
        JSON response indicating success/failure of sending invitation
    """
    event = Event.query.get_or_404(event_id)

    event_details = {
        'event_name': event.name,
        'event_date': event.date.strftime('%B %d, %Y'),
        'event_time': event.time.strftime('%I:%M %p'),
        'event_location': event.location
    }

    success = send_invitation_email(email, event_details)

    if success:
        return {'message': 'Invitation sent successfully'}, 200
    else:
        return {'message': 'Failed to send invitation'}, 500
