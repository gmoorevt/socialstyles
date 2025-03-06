from flask import Blueprint

assessment = Blueprint('assessment', __name__)

from . import views
