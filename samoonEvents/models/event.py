"""Event model module.

This module defines the Event model and related enums for managing events in the application.
It handles event data, relationships, and provides methods for budget management, task tracking,
and guest management.

Classes:
    EventStatus: Enum defining possible event statuses
    Event: SQLAlchemy model for events
"""
from ..extensions import db
from datetime import datetime
from enum import Enum as PythonEnum
from .guest import Guest
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import Enum as SqlAlchemyEnum
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship
from .vendor import event_vendors


class EventStatus(PythonEnum):
    """Event status enum.

    Defines the possible states an event can be in:
        ACTIVE: Event is currently active/ongoing
        CANCELLED: Event has been cancelled
        COMPLETED: Event has completed
    """
    ACTIVE = 'active'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'

class Event(db.Model):
    """Event model class.

    Represents an event in the system with properties for tracking details,
    budget, guests, tasks and vendors.

    Attributes:
        event_id (int): Primary key
        owner_id (int): Foreign key to User table
        location (str): Event location
        description (str): Event description
        date (date): Event date
        name (str): Event name
        status (EventStatus): Current event status
        budget (float): Total event budget
        spent_budget (float): Amount spent from budget
        expenses (dict): Tracked expenses

    Relationships:
        owner: Event owner (User)
        guests: Event guests (Guest)
        invitations: Event invitations (Invitation)
        tasks: Event tasks (Task)
        vendors: Event vendors (Vendor)
    """
    __tablename__ = 'Event'

    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)

    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(4082), nullable=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    name = db.Column(db.String(45), nullable=False)
    status = db.Column(SqlAlchemyEnum(EventStatus), default=EventStatus.ACTIVE, nullable=False)
    budget = db.Column(db.Float, default=0.0, nullable=False)
    spent_budget = db.Column(db.Float, default=0.0, nullable=False)
    expenses = db.Column(MutableDict.as_mutable(JSON()), default=dict, nullable=False)


    owner = relationship('User', back_populates='events')
    guests = relationship('Guest', back_populates='event')
    invitations = relationship('Invitation', back_populates='event')
    tasks = relationship('Task', back_populates='event')
    vendors = db.relationship('Vendor',
                            secondary=event_vendors,
                            backref=db.backref('vendor_events', lazy='dynamic'))

    def __init__(self, *args, **kwargs):
        """Initialize event with empty expenses if not provided."""
        super().__init__(*args, **kwargs)
        if self.expenses is None:
            self.expenses = {}

    def serialize(self):
        """Convert event to dictionary for JSON serialization.

        Returns:
            dict: Serialized event data
        """
        return {
            'event_id': self.event_id,
            'name': self.name,
            'description': self.description,
            'date': self.date.isoformat() if self.date else None,
            'location': self.location,
            'owner_id': self.owner_id,
            'status': self.status.value if self.status else None,
            'budget': self.budget or 0.0,
            'expenses': self.expenses or {},
            'spent_budget': self.spent_budget or 0.0
        }

    def add_expense(self, description, amount):
        """Add an expense to the event.

        Args:
            description (str): Expense description
            amount (float): Expense amount

        Raises:
            ValueError: If expense exceeds remaining budget
        """
        if amount > self.remaining_budget:
            raise ValueError("Expense amount exceeds remaining budget")

        if description in self.expenses:
            self.expenses[description] += amount
        else:
            self.expenses[description] = amount

        self.spent_budget += amount
        db.session.commit()

    def __repr__(self):
        """Return string representation of event."""
        return f'<Event {self.name} on {self.date}>'

    def update_vendor_status(self, vendor_id, new_status):
        """Update a vendor's status for this event.

        Args:
            vendor_id (int): ID of vendor to update
            new_status (str): New status value

        Returns:
            bool: True if update successful, False otherwise
        """
        vendor = next((v for v in self.vendors if v.vendor_id == vendor_id), None)
        if vendor and new_status in ['pending', 'confirmed']:
            vendor.status = new_status
            db.session.commit()
            return True
        return False

    @property
    def completed_tasks(self):
        """Get number of completed tasks.

        Returns:
            int: Count of completed tasks
        """
        return sum(1 for task in self.tasks if task.status == 'completed')

    @property
    def total_tasks(self):
        """Get total number of tasks.

        Returns:
            int: Total task count
        """
        return len(self.tasks)

    @property
    def progress(self):
        """Calculate overall planning progress percentage.

        Combines task completion (60% weight) and vendor confirmation (40% weight).

        Returns:
            float: Overall planning progress percentage
        """
        # Calculate task progress (60% of total)
        task_progress = 0
        if self.total_tasks > 0:
            task_progress = (self.completed_tasks / self.total_tasks) * 60

        # Calculate vendor progress (40% of total)
        vendor_progress = 0
        total_vendors = len(self.vendors)
        if total_vendors > 0:
            confirmed_vendors = sum(1 for v in self.vendors if v.status == 'confirmed')
            vendor_progress = (confirmed_vendors / total_vendors) * 40

        # Return combined progress
        return task_progress + vendor_progress

    @property
    def confirmed_guests(self):
        """Get number of confirmed guests.

        Returns:
            int: Count of confirmed guests
        """
        return Guest.query.filter_by(
            event_id=self.event_id,
            status='Attending'
        ).count()

    @property
    def pending_guests(self):
        """Get number of pending guests.

        Returns:
            int: Count of pending guests (includes both Pending and Invited status)
        """
        return Guest.query.filter(
            Guest.event_id == self.event_id,
            Guest.status.in_(['Pending', 'Invited'])
        ).count()

    @property
    def total_guests(self):
        """Get total number of guests.

        Returns:
            int: Total guest count
        """
        return self.confirmed_guests + self.pending_guests

    @property
    def remaining_budget(self):
        """Calculate remaining budget.

        Returns:
            float: Remaining budget amount
        """
        return self.budget - self.spent_budget

    def update_budget(self, new_budget):
        """Update event budget.

        Args:
            new_budget (float): New budget amount

        Raises:
            ValueError: If new budget is less than spent amount
        """
        if new_budget < self.spent_budget:
            raise ValueError("New budget cannot be less than spent budget")
        self.budget = new_budget
        db.session.commit()
