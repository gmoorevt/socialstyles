from flask import Blueprint

team = Blueprint('team', __name__)

from app.team import routes 