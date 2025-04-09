"""Vendor management module.

This module handles all vendor-related operations including:
- Displaying available vendors
- Adding vendors to events
- Updating vendor information
- Removing vendors from events
- Managing vendor-event relationships

The module provides a RESTful API for vendor operations as well as
template rendering for the vendor management interface.
"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from ..views import app_views
from ..models.vendor import Vendor
from ..models.event import Event
from ..models.review import Review
from ..extensions import db
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import text

@app_views.route('/vendors', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def vendors():
    """Handle all vendor management operations.

    Provides CRUD functionality for vendors and vendor-event relationships.
    Requires user authentication.

    Methods:
        GET: Display vendors page or add vendor to event
        POST: Add new vendor to event via AJAX
        PUT: Update existing vendor details
        DELETE: Remove vendor from event

    Returns:
        GET: Rendered template or redirect response
        POST/PUT/DELETE: JSON response with operation result

    Raises:
        404: If event or vendor not found
        403: If user not authorized for operation
        400: If invalid request or operation fails
    """
    if request.method == 'GET':
        # Handle adding vendor to event
        action = request.args.get('action')
        if action == 'add':
            vendor_id = request.args.get('vendor_id')
            event_id = request.args.get('event_id')

            try:
                event = Event.query.get_or_404(event_id)
                vendor = Vendor.query.get_or_404(vendor_id)

                # Verify event ownership
                if event.owner_id != current_user.user_id:
                    flash('Unauthorized access', 'error')
                    return redirect(url_for('app_views.vendors'))

                # Check if vendor is already in event
                if vendor in event.vendors:
                    flash(f'"{vendor.name}" is already added to this event', 'error')
                else:
                    event.vendors.append(vendor)
                    db.session.commit()
                    flash(f'"{vendor.name}" added to event successfully', 'success')

                # Redirect back to vendors page with event_id
                return redirect(url_for('app_views.vendors', event_id=event_id))

            except Exception as e:
                db.session.rollback()
                flash(f'Error adding vendor: {str(e)}', 'error')
                return redirect(url_for('app_views.vendors', event_id=event_id))

        # Regular vendors page display
        context = {
            'vendors': Vendor.query.all(),
            'event_id': request.args.get('event_id')
        }

        # If we're selecting vendors for an event, get the event's current vendors
        if context['event_id']:
            event = Event.query.get(context['event_id'])
            if event:
                context['event_vendors'] = event.vendors

        return render_template('vendors.html', **context)

    elif request.method == 'POST':
        try:
            data = request.json
            event_id = data.get('event_id')
            vendor_id = data.get('vendor_id')

            # Get event and vendor
            event = Event.query.get_or_404(event_id)
            vendor = Vendor.query.get_or_404(vendor_id)

            # Verify event ownership
            if event.owner_id != current_user.user_id:
                return jsonify({'error': 'Unauthorized'}), 403

            # Check if vendor is already in event
            if vendor in event.vendors:
                return jsonify({'error': 'Vendor already added to this event'}), 400

            # Add vendor to event
            event.vendors.append(vendor)
            db.session.commit()

            return jsonify({
                'message': 'Vendor added successfully',
                'vendor': {
                    'id': vendor.vendor_id,
                    'name': vendor.name
                }
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    elif request.method == 'PUT':
        try:
            data = request.json
            vendor_id = data.get('vendor_id')
            vendor = Vendor.query.get_or_404(vendor_id)

            # Verify vendor belongs to user's event
            if not any(event.owner_id == current_user.user_id for event in vendor.events):
                return jsonify({'error': 'Unauthorized'}), 403

            # Update vendor details
            if 'name' in data:
                vendor.name = data['name']
            if 'category' in data:
                vendor.category = data['category']
            if 'description' in data:
                vendor.description = data['description']
            if 'image_path' in data:
                vendor.image_path = data['image_path']
            if 'phone_number' in data:
                vendor.phone_number = data['phone_number']
            if 'email' in data:
                vendor.email = data['email']
            if 'service_fee' in data:
                vendor.service_fee = data['service_fee']
            if 'rating' in data:
                vendor.rating = data['rating']
            if 'status' in data:
                vendor.status = data['status']

            db.session.commit()

            return jsonify({
                'message': 'Vendor updated successfully',
                'vendor': vendor.serialize()
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    elif request.method == 'DELETE':
        try:
            data = request.json
            event_id = data.get('event_id')
            vendor_id = data.get('vendor_id')

            if not event_id or not vendor_id:
                return jsonify({'error': 'Missing event_id or vendor_id'}), 400

            # Get event and vendor
            event = Event.query.get_or_404(event_id)
            vendor = Vendor.query.get_or_404(vendor_id)

            # Verify event ownership
            if event.owner_id != current_user.user_id:
                return jsonify({'error': 'Unauthorized'}), 403

            # Check if relationship exists first
            exists = db.session.execute(
                text("SELECT 1 FROM event_vendors WHERE event_id = :event_id AND vendor_id = :vendor_id"),
                {"event_id": event_id, "vendor_id": vendor_id}
            ).first()

            if not exists:
                return jsonify({'error': 'Vendor not found in event'}), 404

            # Delete the relationship directly
            db.session.execute(
                text("DELETE FROM event_vendors WHERE event_id = :event_id AND vendor_id = :vendor_id"),
                {"event_id": event_id, "vendor_id": vendor_id}
            )
            db.session.commit()

            return jsonify({'message': 'Vendor removed from event successfully'})

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

@app_views.route('/api/reviews', methods=['POST'])
@login_required
def create_review():
    try:
        data = request.get_json()

        if not data or 'vendor_id' not in data or 'rating' not in data or 'comment' not in data:
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if user has already reviewed this vendor
        existing_review = Review.query.filter_by(
            vendor_id=data['vendor_id'],
            user_id=current_user.user_id
        ).first()

        if existing_review:
            return jsonify({'error': 'You have already reviewed this vendor'}), 400

        review = Review(
            vendor_id=data['vendor_id'],
            user_id=current_user.user_id,
            rating=data['rating'],
            comment=data['comment']
        )

        db.session.add(review)
        db.session.commit()

        return jsonify({
            'message': 'Review submitted successfully',
            'review': {
                'user_name': current_user.username,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.strftime('%B %d, %Y') if review.created_at else None
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create review'}), 500

@app_views.route('/api/vendors/<int:vendor_id>/reviews', methods=['GET'])
def get_vendor_reviews(vendor_id):
    try:
        vendor = Vendor.query.get_or_404(vendor_id)
        reviews = []

        for review in vendor.reviews:
            date_str = review.created_at.strftime('%Y-%m-%d') if review.created_at else None
            formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y') if date_str else None

            reviews.append({
                'user_name': review.user.username,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': formatted_date
            })

        return jsonify({
            'vendor_name': vendor.name,
            'reviews': reviews
        })
    except Exception as e:
        print(f"Error fetching reviews: {str(e)}")  # Debug log
        return jsonify({'error': 'Failed to fetch reviews'}), 500
