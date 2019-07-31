"""
Automated tests for the ingestion of the MPL_ORBPRE files

Written by DEIMOS Space S.L. (femd)

module ingestions
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

class TestOrbpre(unittest.TestCase):
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

    def test_orbpre_only(self):

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        #Check sources
        sources = self.query_eboa.get_sources()

        assert len(sources) == 2

        definite_source1 = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-20T03:02:21", "op": "=="}],
                                                       validity_stop_filters = [{"date": "2018-07-30T04:42:21", "op": "=="}],
                                                       generation_time_filters = [{"date": "2018-07-20T03:02:18", "op": "=="}],
                                                       processors = {"filter": "ingestion_orbpre.py", "op": "like"},
                                                       names = {"filter": "S2A_ORBPRE.EOF", "op": "like"},
                                                       dim_signatures = {"filter": "ORBPRE", "op": "like"})

        assert len(definite_source1) == 1

        definite_source2 = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T09:50:51.776833", "op": "=="}],
                                                       validity_stop_filters = [{"date": "2018-07-21T11:31:33.673527", "op": "=="}],
                                                       generation_time_filters = [{"date": "2018-07-20T03:02:18", "op": "=="}],
                                                       processors = {"filter": "ingestion_orbpre.py", "op": "like"},
                                                       names = {"filter": "S2A_ORBPRE.EOF", "op": "like"},
                                                       dim_signatures = {"filter": "CORRECTED_NPPF_S2A", "op": "like"})

        assert len(definite_source2) == 1

        #Check events
        events = self.query_eboa.get_events()

        assert len(events) == 2

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "ORBIT_PREDICTION", "op": "like"},
                                                    start_filters = [{"date": "2018-07-21 09:50:51.776833", "op": "=="}])

        assert definite_event[0].get_structured_values() == [{
            "name": "orbit_information",
            "type": "object",
            "values": [
                {
                    "name": "tai",
                    "type": "timestamp",
                    "value": "2018-07-21T09:51:28.776833"
                },
                {
                    "name": "ut1",
                    "type": "timestamp",
                    "value": "2018-07-21T09:50:51.845800"
                },
                {
                    "name": "orbit",
                    "type": "double",
                    "value": "16078.0"
                },
                {
                    "name": "x",
                    "type": "double",
                    "value": "-7065094.736"
                },
                {
                    "name": "y",
                    "type": "double",
                    "value": "-1221573.823"
                },
                {
                    "name": "z",
                    "type": "double",
                    "value": "0.0"
                },
                {
                    "name": "vx",
                    "type": "double",
                    "value": "-269.810341"
                },
                {
                    "name": "vy",
                    "type": "double",
                    "value": "1610.581671"
                },
                {
                    "name": "vz",
                    "type": "double",
                    "value": "7374.757343"
                },
                {
                    "name": "satellite",
                    "type": "text",
                    "value": "S2A"
                },
                {
                    "name": "quality",
                    "type": "double",
                    "value": "0.0"
                }
            ]            
        }]

    def test_obrpre_with_plan(self):

        previous_logging_level = None
        if "EBOA_LOG_LEVEL" in os.environ:
            previous_logging_level = os.environ["EBOA_LOG_LEVEL"]
        # end if

        # Set log level to INFO to avoid the value get_footprint_command
        os.environ["EBOA_LOG_LEVEL"] = "INFO"
        
        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        #Check sources
        sources = self.query_eboa.get_sources()

        assert len(sources) == 3

        definite_source1 = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-20T03:02:21", "op": "=="}],
                                                       validity_stop_filters = [{"date": "2018-07-30T04:42:21", "op": "=="}],
                                                       generation_time_filters = [{"date": "2018-07-20T03:02:18", "op": "=="}],
                                                       processors = {"filter": "ingestion_orbpre.py", "op": "like"},
                                                       names = {"filter": "S2A_ORBPRE.EOF", "op": "like"},
                                                       dim_signatures = {"filter": "ORBPRE", "op": "like"})

        assert len(definite_source1) == 1

        definite_source2 = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T09:50:51.776833", "op": "=="}],
                                                       validity_stop_filters = [{"date": "2018-07-21T11:31:33.673527", "op": "=="}],
                                                       generation_time_filters = [{"date": "2018-07-20T03:02:18", "op": "=="}],
                                                       processors = {"filter": "ingestion_orbpre.py", "op": "like"},
                                                       names = {"filter": "S2A_ORBPRE.EOF", "op": "like"},
                                                       dim_signatures = {"filter": "CORRECTED_NPPF_S2A", "op": "like"})

        assert len(definite_source2) == 1

        definite_source3 = self.query_eboa.get_sources(names = {"filter": "S2A_NPPF.EOF", "op": "like"})

        assert len(definite_source3) == 1
        
        #Check events
        events = self.query_eboa.get_events()

        assert len(events) == 8

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_PLAYBACK_CORRECTION", "op": "like"},
                                                    start_filters = [{"date": "2018-07-21T10:37:19.534390", "op": "=="}])

        assert definite_event[0].get_structured_values() == [{
            "name": "details",
            "type": "object",
            "values": [
                {
                    "name": "start_request",
                    "type": "text",
                    "value": "MPMMPBSA"
                },
                {
                    "name": "stop_request",
                    "type": "text",
                    "value": "MPMMPBSA"
                },
                {
                    "name": "start_orbit",
                    "type": "double",
                    "value": "16078.0"
                },
                {
                    "name": "start_angle",
                    "type": "double",
                    "value": "166.2002"
                },
                {
                    "name": "stop_orbit",
                    "type": "double",
                    "value": "16078.0"
                },
                {
                    "name": "stop_angle",
                    "type": "double",
                    "value": "166.2002"
                },
                {
                    "name": "satellite",
                    "type": "text",
                    "value": "S2A"
                },
                {
                    "name": "playback_mean",
                    "type": "text",
                    "value": "XBAND"
                },
                {
                    "name": "playback_type",
                    "type": "text",
                    "value": "SAD"
                },
                {
                    "name": "parameters",
                    "type": "object",
                    "values": [
                        {
                            "name": "MEM_FREE",
                            "type": "double",
                            "value": "0.0"
                        }
                    ]
                },
                {
                    "name": "status_correction",
                    "type": "text",
                    "value": "TIME_CORRECTED"
                },
                {
                    "name": "delta_start",
                    "type": "double",
                    "value": "-5.10339"
                },
                {
                    "name": "delta_stop",
                    "type": "double",
                    "value": "-5.10339"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((1.562179 13.283699, -1.035809 13.852637, -1.035809 13.852637, 1.562179 13.283699))"
                        }
                    ]
                }
            ]
        }]

        if previous_logging_level:
            os.environ["EBOA_LOG_LEVEL"] = previous_logging_level
        else:
            del os.environ["EBOA_LOG_LEVEL"]
        # end if
