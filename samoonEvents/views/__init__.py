from flask import Blueprint

app_views = Blueprint('app_views', __name__)

# Import all routes AFTER creating the blueprint
from .views import *
from .guest import *
from .email import *
from .dashboard import *
from .profile import *
from .vendors import *
from .auth import *
