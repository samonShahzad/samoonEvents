# samoonEvents

samoonEvents is a comprehensive event planning and management web application built with Flask. It enables users to create, organize, and manage events, handle guest lists, track RSVPs, coordinate with vendors, and monitor budgets—all in one place.

![samoonEvents](https://images.unsplash.com/photo-1512453979798-5ea266f8880c?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80)

## Features

- **User Authentication**: Secure signup, login, and profile management
- **Event Management**: Create, edit, and delete events with detailed information
- **Guest Management**: Add guests, send invitations, and track RSVPs
- **Vendor Coordination**: Browse and book vendors, manage their status, and read reviews
- **Task Tracking**: Create and monitor tasks to stay organized
- **Budget Management**: Set budgets and track expenses
- **Responsive Design**: Beautiful interface that works on desktop and mobile devices

## Tech Stack

- **Backend**: Python 3.x, Flask 2.2.5
- **Database**: SQLAlchemy with SQLite support (can be configured for MySQL)
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Authentication**: Flask-Login
- **Email**: Flask-Mail
- **Database Migrations**: Flask-Migrate and Alembic

## Installation

### Prerequisites

- Python 3.7+
- pip

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/samoonEvents.git
   cd samoonEvents
   ```

2. Set up a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your environment variables by creating a `.env` file:
   ```
   SECRET_KEY=your-secret-key

   # Database configuration (use these for MySQL)
   # DB_USER=username
   # DB_PASSWORD=password
   # DB_HOST=localhost
   # DB_NAME=samoonevents

   # Email configuration
   MAIL_SERVER=smtp.example.com
   MAIL_PORT=465
   MAIL_USE_SSL=True
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-email-password
   MAIL_DEFAULT_SENDER=your-email@example.com
   ```

5. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. Generate sample data (optional):
   ```
   python -c "from samoonEvents.samoonEvents.generate_data import create_data; from samoonEvents.samoonEvents.app import app; with app.app_context(): create_data()"
   ```

## Running the Application

1. Start the development server:
   ```
   flask run
   ```

2. Open your browser and navigate to `http://localhost:5000`

## Project Structure

```
samoonEvents/
├── .venv/                  # Virtual environment folder
├── documentation/          # Project documentation
├── samoonEvents/           # Main package
│   ├── __init__.py         # Package initialization
│   ├── app.py              # Application factory
│   ├── config.py           # Configuration
│   ├── extensions.py       # Flask extensions
│   ├── generate_data.py    # Sample data generation
│   ├── LICENSE             # MIT license
│   ├── models/             # Database models
│   │   ├── __init__.py
│   │   ├── event.py
│   │   ├── guest.py
│   │   ├── invitation.py
│   │   ├── review.py
│   │   ├── task.py
│   │   ├── user.py
│   │   └── vendor.py
│   ├── static/             # Static files
│   │   └── images/         # Image uploads and defaults
│   ├── templates/          # HTML templates
│   └── views/              # View functions
│       ├── __init__.py
│       ├── auth.py
│       ├── dashboard.py
│       ├── email.py
│       ├── guest.py
│       ├── profile.py
│       ├── vendors.py
│       └── views.py
├── requirements.txt        # Dependencies
└── wsgi.py                 # WSGI entry point
```

## Usage

### Creating an Event

1. Sign up or log in to your account
2. Navigate to the Events page
3. Click "Create New Event"
4. Fill in the event details (name, date, location, budget)
5. Add tasks, guests, and vendors as needed

### Managing Guests

1. Go to your event details page
2. Navigate to the "Guest List" tab
3. Add guests with their email addresses
4. Send invitations to guests
5. Track RSVPs in real-time

### Working with Vendors

1. Browse available vendors in the Vendors section
2. Add vendors to your event
3. Update vendor status (pending, confirmed)
4. View and write reviews for vendors

## Security Features

- Password hashing using Werkzeug's security functions
- CSRF protection
- Secure session handling
- Input validation and sanitization
- User-specific access controls

## Development

### Setting Up Development Environment

1. Follow the installation steps above
2. Install additional development dependencies:
   ```
   pip install pytest coverage
   ```

### Running Tests

```
pytest
```

Or with coverage:

```
coverage run -m pytest
coverage report
```

## Deployment

For production deployment:

1. Configure a production-ready WSGI server like Gunicorn:
   ```
   gunicorn "samoonEvents.app:app"
   ```

2. Configure a proper database like MySQL or PostgreSQL

3. Set up a reverse proxy with Nginx or Apache

4. Use HTTPS with a valid SSL certificate

## License

This project is licensed under the MIT License - see the [LICENSE](samoonEvents/LICENSE) file for details.

## Acknowledgements

- Development by the samoonEvents Team
- Tailwind CSS for responsive styling
- Unsplash for demo images
- Flask and its extension authors

## Contact

For any questions or issues, please contact us at 35562778@student.murdoch.edu.au

---

**Note:** samoonEvents is an educational project created in 2025 at Murdoch University, Dubai.
