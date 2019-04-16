"""
Vies navigation section definition

Written by DEIMOS Space S.L. (dibb)

module s2vboa
"""
# Import python utilities
import sys
import json
# Import flask utilities
from flask import Blueprint, flash, g, current_app, redirect, render_template, request, url_for
from flask_debugtoolbar import DebugToolbarExtension
from flask import jsonify

# Import eboa utilities
from eboa.engine.query import Query
import eboa.engine.engine as eboa_engine
from eboa.engine.engine import Engine

bp = Blueprint("views", __name__, url_prefix="/views")
query = Query()
engine = Engine()

@bp.route("/planning", methods=["GET"])
def navigate():
    """
    Initial panel for the EBOA navigation functionality.
    """
    return render_template("views/planning.html")

