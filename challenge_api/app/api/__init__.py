from flask import Blueprint

# Create blueprint
v1 = Blueprint('v1', __name__, url_prefix='/api/v1')
