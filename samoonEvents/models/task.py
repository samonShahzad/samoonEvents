"""Task model module.

This module defines the Task model for managing event-related tasks in the application.
It handles task data, relationships with events, and provides methods for serialization
and string representation.

Classes:
    Task: SQLAlchemy model for tasks
"""
from ..extensions import db

class Task(db.Model):
    """Task model class.

    Represents a task associated with an event in the system.

    Attributes:
        task_id (int): Primary key
        description (str): Task description
        status (str): Current task status, defaults to 'pending'
        event_id (int): Foreign key to Event table
        due_date (date): Task due date

    Relationships:
        event: Associated event (Event)
    """
    __tablename__ = 'Task'

    task_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending')
    event_id = db.Column(db.Integer, db.ForeignKey('Event.event_id'), nullable=False)
    due_date = db.Column(db.Date, nullable=False)

    event = db.relationship('Event', back_populates='tasks')

    def serialize(self):
        """Convert task instance to dictionary for JSON serialization.

        Returns:
            dict: Dictionary containing task data
        """
        return {
            'task_id': self.task_id,
            'description': self.description,
            'status': self.status,
            'event_id': self.event_id,
            'due_date': self.due_date.isoformat() if self.due_date else None,
        }

    def __repr__(self):
        """String representation of Task instance.

        Returns:
            str: Task description and status
        """
        return f'<Task {self.description} (Status: {self.status})>'
