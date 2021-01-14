"""
Specific instantiation for the S2 visualization tool

Written by DEIMOS Space S.L. (dibb)

module s2vboa
"""
# Import python utilities
import os

# Import flask utilities
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
import jinja2

# Import vboa
import vboa
from s2vboa.views import planning
from s2vboa.views import hktm_workflow
from s2vboa.views import acquisition
from s2vboa.views import processing
from s2vboa.views import tracking
from s2vboa.views import dhus_completeness
from s2vboa.views import sensing_data_volumes
from s2vboa.views import archive_data_volumes
from s2vboa.views import detailed_processing_timeliness

def create_app():
    """
    Create and configure an instance of vboa application.
    """
    app = vboa.create_app()

    app.register_blueprint(planning.bp)
    app.register_blueprint(hktm_workflow.bp)
    app.register_blueprint(acquisition.bp)
    app.register_blueprint(processing.bp)
    app.register_blueprint(tracking.bp)
    app.register_blueprint(dhus_completeness.bp)
    app.register_blueprint(sensing_data_volumes.bp)
    app.register_blueprint(archive_data_volumes.bp)
    app.register_blueprint(detailed_processing_timeliness.bp)

    s2vboa_templates_folder = os.path.dirname(__file__) + "/templates"

    templates_loader = jinja2.ChoiceLoader([
        jinja2.FileSystemLoader(s2vboa_templates_folder),
        app.jinja_loader
    ])
    app.jinja_loader = templates_loader
    
    return app
