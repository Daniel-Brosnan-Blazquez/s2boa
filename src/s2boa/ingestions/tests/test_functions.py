"""
Automated tests for the functions of the ingestion of the S2BOA submodule

Written by DEIMOS Space S.L. (dibb)

module s2boa
"""
# Import python utilities
import os
import sys
import unittest
import datetime
from dateutil import parser

# Import engine of the DDBB
import eboa.engine.engine as eboa_engine
from eboa.engine.engine import Engine
from eboa.engine.query import Query

# Import ingestion
import eboa.ingestion.eboa_ingestion as ingestion

# Import functions
import s2boa.ingestions.functions as s2boa_functions

class TestS2boaFunctions(unittest.TestCase):
    def setUp(self):
        # Create the engine to manage the data
        self.engine_eboa = Engine()
        self.query_eboa = Query()

        # Clear all tables before executing the test
        self.query_eboa.clear_db()

    def tearDown(self):
        # Close connections to the DDBB
        self.engine_eboa.close_session()
        self.query_eboa.close_session()

    def test_associate_footprint_covered_by_one_orbpre_event(self):

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        events = [
            {"gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "GAUGE_NAME",
                "system": "GAUGE_SYSTEM"
            },
             "start": "2018-07-21T09:50:51.776833",
             "stop": "2018-07-21T09:50:51.776833",
            }

        ]

        events_with_footprint = s2boa_functions.associate_footprints(events, "S2A")

        assert events_with_footprint == [{
            'gauge': {'insertion_type': 'SIMPLE_UPDATE',
                      'name': 'GAUGE_NAME',
                      'system': 'GAUGE_SYSTEM'},
            'start': '2018-07-21T09:50:51.776833',
            'stop': '2018-07-21T09:50:51.776833',
            'values': [{'name': 'details',
                        'type': 'object',
                        'values': [{'name': 'footprint_details',
                                    'type': 'object',
                                    'values': [{'name': 'footprint',
                                                'type': 'geometry',
                                                'value': '-171.455147 -0.281921 -168.925664 0.281908 -168.925664 0.281908 -171.455147 -0.281921'}
                                    ]}
                        ]}
            ]}
        ]

    def test_associate_footprint_not_covered_by_orbpre_event(self):

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        events = [
            {"gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "GAUGE_NAME",
                "system": "GAUGE_SYSTEM"
            },
             "start": "2018-07-21T08:50:51.776833",
             "stop": "2018-07-21T09:50:51.776833",
            }

        ]

        events_with_footprint = s2boa_functions.associate_footprints(events, "S2A")

        assert events_with_footprint == [{
            'gauge': {'insertion_type': 'SIMPLE_UPDATE',
                      'name': 'GAUGE_NAME',
                      'system': 'GAUGE_SYSTEM'},
            'start': '2018-07-21T08:50:51.776833',
            'stop': '2018-07-21T09:50:51.776833'
            }
        ]
