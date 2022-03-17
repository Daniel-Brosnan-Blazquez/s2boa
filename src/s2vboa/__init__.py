"""
Specific instantiation for the S2 visualization tool

Written by DEIMOS Space S.L. (dibb)

module s2vboa
"""
# Import python utilities
import os

# Import flask utilities
from flask import Flask, send_from_directory
from flask_debugtoolbar import DebugToolbarExtension
import jinja2

# Import vboa
import vboa

# Import views
from s2vboa.views.planning import planning
from s2vboa.views.data_allocation import data_allocation
from s2vboa.views.hktm_workflow import hktm_workflow
from s2vboa.views.acquisition import acquisition
from s2vboa.views.datatake_completeness import datatake_completeness
from s2vboa.views.processing import processing
from s2vboa.views.tracking import tracking
from s2vboa.views.dhus_completeness import dhus_completeness
from s2vboa.views.sensing_data_volumes import sensing_data_volumes
from s2vboa.views.archive_data_volumes import archive_data_volumes
from s2vboa.views.detailed_processing_timeliness import detailed_processing_timeliness

def create_app():
    """
    Create and configure an instance of vboa application.
    """
    app = vboa.create_app()

    # Register the specific views
    app.register_blueprint(planning.bp)
    app.register_blueprint(data_allocation.bp)
    app.register_blueprint(hktm_workflow.bp)
    app.register_blueprint(acquisition.bp)
    app.register_blueprint(datatake_completeness.bp)
    app.register_blueprint(processing.bp)
    app.register_blueprint(tracking.bp)
    app.register_blueprint(dhus_completeness.bp)
    app.register_blueprint(sensing_data_volumes.bp)
    app.register_blueprint(archive_data_volumes.bp)
    app.register_blueprint(detailed_processing_timeliness.bp)

    # Register the specific templates folder
    s2vboa_templates_folder = os.path.dirname(__file__) + "/templates"
    templates_loader = jinja2.ChoiceLoader([
        jinja2.FileSystemLoader(s2vboa_templates_folder),
        app.jinja_loader
    ])
    app.jinja_loader = templates_loader

    # Register the specific static folder
    s2vboa_static_folder = os.path.dirname(__file__) + "/static"
    @app.route('/s2_static_images/<path:filename>')
    def s2_static(filename):
        return send_from_directory(s2vboa_static_folder + "/images", filename)
    # end def
    
    return app
