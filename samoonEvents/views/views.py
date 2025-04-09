"""Event management views module.

This module handles all event-related operations including:
- Creating, reading, updating and deleting events
- Managing event expenses and budgets
- Handling event tasks and vendor assignments
- Processing vendor status updates

The routes in this module require authentication and enforce ownership checks
to ensure users can only access their own events.
"""

from datetime import datetime
from flask import render_template, redirect, url_for, flash, jsonify, request, current_app
from flask_login import login_required, current_user
from ..extensions import db
from ..models.event import Event, EventStatus
from ..models.vendor import event_vendors
from ..models.task import Task
from ..models.guest import Guest
from ..models.invitation import Invitation
from ..views import app_views

@app_views.route('/events', methods=['GET', 'POST'])
@login_required
def events():
    """Handle event listing and creation."""
    if request.method == 'POST':
        try:
            data = request.form

            # Validate required fields
            required_fields = ['name', 'date', 'location']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({
                        'success': False,
                        'error': f'{field.capitalize()} is required'
                    }), 400

            # Convert and validate budget
            try:
                budget = float(data.get('budget', 0))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid budget value'
                }), 400

            new_event = Event(
                owner_id=current_user.user_id,
                name=data.get('name'),
                date=datetime.strptime(data.get('date'), '%Y-%m-%d').date(),
                location=data.get('location'),
                description=data.get('description', ''),
                status=EventStatus.ACTIVE,
                budget=budget,
                spent_budget=0.0,
                expenses={}
            )

            db.session.add(new_event)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Event created successfully',
                'event': new_event.serialize()
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    # GET request
    user_id = current_user.user_id
    events = Event.query.filter_by(owner_id=user_id).all()
    serialized_events = [event.serialize() for event in events]
    return render_template('events.html', events=serialized_events)


@app_views.route('/event/<int:event_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def event_details(event_id):
    """Handle operations on a specific event.

    GET: Display event details
    PUT: Update event details
    DELETE: Remove event and all associated data

    Args:
        event_id: ID of event to operate on

    Returns:
        GET: Rendered event details template
        PUT/DELETE: JSON response with operation result
    """
    try:
        event = Event.query.get_or_404(event_id)

        # Check ownership
        if event.owner_id != current_user.user_id:
            return jsonify({
                'success': False,
                'error': 'You do not have permission to access this event'
            }), 403

        if request.method == 'GET':
            return render_template('event_details.html', event=event, EventStatus=EventStatus)

        elif request.method == 'PUT':
            data = request.get_json() if request.is_json else request.form

            event.name = data['name']
            event.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            event.location = data['location']
            event.description = data['description']
            event.status = EventStatus(data['status']) if 'status' in data else event.status

            if 'budget' in data:
                try:
                    new_budget = float(data['budget'])
                    if new_budget < event.spent_budget:
                        return jsonify({
                            'success': False,
                            'error': 'New budget cannot be less than spent budget'
                        }), 400
                    event.budget = new_budget
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid budget value'
                    }), 400

            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Event updated successfully',
                'event': event.serialize()
            })

        elif request.method == 'DELETE':
            try:
                # First, remove all vendor associations
                db.session.execute(
                    event_vendors.delete().where(event_vendors.c.event_id == event_id)
                )

                # Delete tasks associated with the event
                Task.query.filter_by(event_id=event_id).delete()

                # Delete invitations if they exist
                if hasattr(event, 'invitations'):
                    Invitation.query.filter_by(event_id=event_id).delete()

                # Delete guests if they exist
                if hasattr(event, 'guests'):
                    Guest.query.filter_by(event_id=event_id).delete()

                # Finally delete the event
                db.session.delete(event)
                db.session.commit()

                return jsonify({
                    'success': True,
                    'message': 'Event deleted successfully'
                })

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error deleting event: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in event_details: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app_views.route('/event/<int:event_id>/expense/<path:category>', methods=['POST', 'PUT', 'DELETE'])
@login_required
def handle_expense(event_id, category):
    """Handle expense operations for an event.

    POST: Add new expense
    PUT: Update existing expense
    DELETE: Remove expense

    Args:
        event_id: ID of event to modify expenses for
        category: Expense category name

    Returns:
        JSON response with updated expense details
    """
    try:
        # Verify event ownership
        event = Event.query.get_or_404(event_id)
        if event.owner_id != current_user.user_id:
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403

        # Initialize expenses dictionary if it doesn't exist
        if not hasattr(event, 'expenses') or event.expenses is None:
            event.expenses = {}

        if request.method == 'DELETE':
            # Delete expense - no need to parse JSON for DELETE
            if category not in event.expenses:
                return jsonify({'success': False, 'error': 'Expense not found'}), 404

            del event.expenses[category]
            message = 'Expense deleted successfully'

        else:
            # POST and PUT methods need JSON data
            data = request.get_json()

            if request.method == 'PUT':
                # Update expense
                new_category = data.get('category')
                new_amount = data.get('amount')

                if not new_category or new_amount is None:
                    return jsonify({'success': False, 'error': 'Missing required fields'}), 400

                # Update the expense
                if category != new_category:
                    del event.expenses[category]
                event.expenses[new_category] = new_amount
                message = 'Expense updated successfully'

            elif request.method == 'POST':
                # Add expense
                amount = data.get('amount')
                if amount is None:
                    return jsonify({'success': False, 'error': 'Missing amount'}), 400

                event.expenses[category] = amount
                message = 'Expense added successfully'

        # Update total spent budget
        event.spent_budget = sum(event.expenses.values())
        db.session.commit()

        return jsonify({
            'success': True,
            'message': message,
            'total_spent': event.spent_budget,
            'expenses': event.expenses
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error handling expense: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app_views.route('/event/<int:event_id>/update_vendor_status/<int:vendor_id>', methods=['POST'])
@login_required
def update_vendor_status(event_id, vendor_id):
    """Update vendor status for an event.

    Args:
        event_id: ID of event containing vendor
        vendor_id: ID of vendor to update

    Returns:
        JSON response for AJAX requests or redirect for form submissions
    """
    try:
        event = Event.query.get_or_404(event_id)

        # Check if the current user is the event owner
        if event.owner_id != current_user.user_id:
            message = 'You do not have permission to update vendor status for this event.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message}), 403
            flash(message, 'error')
            return redirect(url_for('app_views.event_details', event_id=event_id))

        new_status = request.form.get('status')
        if event.update_vendor_status(vendor_id, new_status):
            message = f'Vendor status updated to {new_status}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': message})
            flash(message, 'success')
        else:
            message = 'Failed to update vendor status'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message}), 400
            flash(message, 'error')

        # For regular form submissions, redirect back to the appropriate page
        referrer = request.referrer
        if referrer and 'dashboard' in referrer:
            return redirect(url_for('app_views.dashboard'))
        return redirect(url_for('app_views.event_details', event_id=event_id))

    except Exception as e:
        message = 'Error updating vendor status'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': message}), 500
        flash(message, 'error')
        return redirect(url_for('app_views.dashboard'))


@app_views.route('/event/<int:event_id>/tasks', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def tasks(event_id):
    """Handle task operations for an event.

    GET: List all tasks
    POST: Create new task
    PUT: Update existing task
    DELETE: Remove task

    Args:
        event_id: ID of event to manage tasks for

    Returns:
        JSON response with task operation results
    """
    try:
        event = Event.query.get_or_404(event_id)
        if event.owner_id != current_user.user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        if request.method == 'POST':
            # Create new task
            data = request.json
            new_task = Task(
                event_id=event_id,
                description=data['name'],
                due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
                status='pending'
            )

            db.session.add(new_task)
            db.session.commit()

            flash('Task created successfully!', 'success')
            return jsonify({
                'success': True,
                'message': 'Task created successfully',
                'task': new_task.serialize()
            })

        elif request.method == 'PUT':
            # Update existing task
            data = request.json
            task_id = data.get('task_id')
            if not task_id:
                return jsonify({'error': 'Task ID is required'}), 400

            task = Task.query.get_or_404(task_id)
            if task.event_id != event_id:
                return jsonify({'error': 'Task not found in this event'}), 404

            if 'name' in data:
                task.description = data['name']
            if 'description' in data:
                task.description = data['description']
            if 'due_date' in data:
                task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
            if 'status' in data:
                old_status = task.status
                task.status = data['status']
                status_message = f'Task marked as {data["status"]}'

            db.session.commit()

            return jsonify({
                'success': True,
                'message': status_message if 'status' in data else 'Task updated successfully',
                'task': task.serialize(),
                'flash': {
                    'message': status_message if 'status' in data else 'Task updated successfully',
                    'type': 'success'
                }
            })

        elif request.method == 'DELETE':
            # Delete task
            data = request.json
            task_id = data.get('task_id')
            if not task_id:
                return jsonify({'error': 'Task ID is required'}), 400

            task = Task.query.get_or_404(task_id)
            if task.event_id != event_id:
                return jsonify({'error': 'Task not found in this event'}), 404

            db.session.delete(task)
            db.session.commit()
            flash('Task deleted successfully', 'success')
            return jsonify({
                'success': True,
                'message': 'Task deleted successfully'
            })

        elif request.method == 'GET':
            # Return all tasks for the event
            tasks = Task.query.filter_by(event_id=event_id).all()
            return jsonify({
                'success': True,
                'tasks': [task.serialize() for task in tasks]
            })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
