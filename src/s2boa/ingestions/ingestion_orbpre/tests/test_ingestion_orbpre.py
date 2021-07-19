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

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        #Check sources
        sources = self.query_eboa.get_sources()

        assert len(sources) == 1

        definite_source1 = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-20T03:02:21", "op": "=="}],
                                                       validity_stop_filters = [{"date": "2018-07-30T04:42:21", "op": "=="}],
                                                       generation_time_filters = [{"date": "2018-07-17T03:02:18", "op": "=="}],
                                                       processors = {"filter": "ingestion_orbpre.py", "op": "like"},
                                                       names = {"filter": "S2A_ORBPRE.EOF", "op": "like"},
                                                       dim_signatures = {"filter": "ORBPRE", "op": "like"})

        assert len(definite_source1) == 1

        #Check events
        events = self.query_eboa.get_events()

        assert len(events) == 2

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "ORBIT_PREDICTION", "op": "like"},
                                                    start_filters = [{"date": "2018-07-21 09:50:51.776833", "op": "=="}])

        assert definite_event[0].get_structured_values() == [
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

    def test_orbpre_with_plan(self):

        previous_logging_level = None
        if "EBOA_LOG_LEVEL" in os.environ:
            previous_logging_level = os.environ["EBOA_LOG_LEVEL"]
        # end if

        # Set log level to INFO to avoid the value get_footprint_command
        os.environ["EBOA_LOG_LEVEL"] = "INFO"
        
        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        #Check sources
        sources = self.query_eboa.get_sources()

        assert len(sources) == 5

        definite_source1 = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-20T03:02:21", "op": "=="}],
                                                       validity_stop_filters = [{"date": "2018-07-30T04:42:21", "op": "=="}],
                                                       generation_time_filters = [{"date": "2018-07-17T03:02:18", "op": "=="}],
                                                       processors = {"filter": "ingestion_orbpre.py", "op": "like"},
                                                       names = {"filter": "S2A_ORBPRE.EOF", "op": "like"},
                                                       dim_signatures = {"filter": "ORBPRE", "op": "like"})

        assert len(definite_source1) == 1

        definite_source2 = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T09:50:51.776833", "op": "=="}],
                                                       validity_stop_filters = [{"date": "2018-07-21T11:31:33.673527", "op": "=="}],
                                                       generation_time_filters = [{"date": "2018-07-17T03:02:18", "op": "=="}],
                                                       processors = {"filter": "ingestion_orbpre.py", "op": "like"},
                                                       names = {"filter": "S2A_ORBPRE.EOF", "op": "like"},
                                                       dim_signatures = {"filter": "CORRECTED_NPPF_S2A", "op": "like"})

        assert len(definite_source2) == 1

        definite_source3 = self.query_eboa.get_sources(names = {"filter": "S2A_NPPF.EOF", "op": "like"})

        assert len(definite_source3) == 2
        
        #Check events
        events = self.query_eboa.get_events()

        assert len(events) == 15

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_PLAYBACK_CORRECTION", "op": "like"},
                                                    start_filters = [{"date": "2018-07-21T10:37:19.534390", "op": "=="}])

        assert definite_event[0].get_structured_values() == [
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

        if previous_logging_level:
            os.environ["EBOA_LOG_LEVEL"] = previous_logging_level
        else:
            del os.environ["EBOA_LOG_LEVEL"]
        # end if

    def test_orbpre_with_plan_first_orbpre(self):

        previous_logging_level = None
        if "EBOA_LOG_LEVEL" in os.environ:
            previous_logging_level = os.environ["EBOA_LOG_LEVEL"]
        # end if

        # Set log level to INFO to avoid the value get_footprint_command
        os.environ["EBOA_LOG_LEVEL"] = "INFO"
        
        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        #Check sources
        sources = self.query_eboa.get_sources()

        assert len(sources) == 4

        definite_source1 = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-20T03:02:21", "op": "=="}],
                                                       reported_validity_stop_filters = [{"date": "2018-07-30T03:02:21", "op": "=="}],
                                                       validity_start_filters = [{"date": "2018-07-20T03:02:21", "op": "=="}],
                                                       validity_stop_filters = [{"date": "2018-07-30T04:42:21", "op": "=="}],
                                                       generation_time_filters = [{"date": "2018-07-17T03:02:18", "op": "=="}],
                                                       processors = {"filter": "ingestion_orbpre.py", "op": "like"},
                                                       names = {"filter": "S2A_ORBPRE.EOF", "op": "like"},
                                                       dim_signatures = {"filter": "ORBPRE", "op": "like"})

        assert len(definite_source1) == 1

        definite_source3 = self.query_eboa.get_sources(names = {"filter": "S2A_NPPF.EOF", "op": "like"})

        assert len(definite_source3) == 3
        
        #Check events
        events = self.query_eboa.get_events()

        assert len(events) == 15

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_PLAYBACK_CORRECTION", "op": "like"},
                                                    start_filters = [{"date": "2018-07-21T10:37:19.534390", "op": "=="}])

        assert definite_event[0].get_structured_values() == [
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

        if previous_logging_level:
            os.environ["EBOA_LOG_LEVEL"] = previous_logging_level
        else:
            del os.environ["EBOA_LOG_LEVEL"]
        # end if

    def test_alerts_orbpre_with_plan_all_operations(self):

        previous_logging_level = None
        if "EBOA_LOG_LEVEL" in os.environ:
            previous_logging_level = os.environ["EBOA_LOG_LEVEL"]
        # end if

        # Set log level to INFO to avoid the value get_footprint_command
        os.environ["EBOA_LOG_LEVEL"] = "INFO"
        
        filename = "S2A_NPPF_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE_FOR_NPPF_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check number of alerts generated
        event_alerts = self.query_eboa.get_event_alerts()

        assert len(event_alerts) == 55

        # Check number of alerts generated
        kwargs = {}
        kwargs["gauge_names"] = {"filter": "STATION_SCHEDULE_COMPLETENESS", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:02:47.392053", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-15T14:02:38.392053", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0001: MISSING STATION SCHEDULE", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_orbpre.py", "op": "=="}
        alerts_station_schedule = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_station_schedule) == 1

        assert alerts_station_schedule[0].message == "The NOMINAL planned playback (with timings: 2018-07-20T14:02:38.392053_2018-07-20T14:14:20.241401) over orbit 16066 is not covered by any station schedule"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_1", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:02:47.392053", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:02:38.392053", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0010: MISSING PLANNED PLAYBACK CH 1", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_orbpre.py", "op": "=="}
        alerts_playback = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_playback) == 1

        assert alerts_playback[0].message == "The NOMINAL planned playback (with timings: 2018-07-20T14:02:38.392053_2018-07-20T14:14:20.241401) over orbit 16066, expected to be received through channel 1, has not been received"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:02:47.392053", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:02:38.392053", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0011: MISSING PLANNED PLAYBACK CH 2", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_orbpre.py", "op": "=="}
        alerts_playback = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_playback) == 1

        assert alerts_playback[0].message == "The NOMINAL planned playback (with timings: 2018-07-20T14:02:38.392053_2018-07-20T14:14:20.241401) over orbit 16066, expected to be received through channel 2, has not been received"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:07:42.793311", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:07:32.793311", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0020: MISSING PLANNED IMAGING CH 1", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_orbpre.py", "op": "=="}
        alerts_imaging = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_imaging) == 1

        assert alerts_imaging[0].message == "The part of the NOMINAL planned imaging (with timings: 2018-07-20T14:07:32.793311_2018-07-20T14:08:58.407047) over orbit 16066 corresponding to channel 1 has not been received"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_2", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:07:42.793311", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:07:32.793311", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0021: MISSING PLANNED IMAGING CH 2", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_orbpre.py", "op": "=="}
        alerts_imaging = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_imaging) == 1

        assert alerts_imaging[0].message == "The part of the NOMINAL planned imaging (with timings: 2018-07-20T14:07:32.793311_2018-07-20T14:08:58.407047) over orbit 16066 corresponding to channel 2 has not been received"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:07:42.793311", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:07:32.793311", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0030: MISSING L0 PROCESSING", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_orbpre.py", "op": "=="}
        alerts_l0_processing = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_l0_processing) == 1

        assert alerts_l0_processing[0].message == "The L0 processing for the NOMINAL planned imaging (with timings: 2018-07-20T14:07:32.793311_2018-07-20T14:08:58.407047) over orbit 16066 has not been performed"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1A", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:10:12.951732", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:10:02.951732", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0031: MISSING L1A PROCESSING", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_orbpre.py", "op": "=="}
        alerts_l1a_processing = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_l1a_processing) == 1

        assert alerts_l1a_processing[0].message == "The L1A processing for the SUN_CAL planned imaging (with timings: 2018-07-20T14:10:02.951732_2018-07-20T14:16:10.071190) over orbit 16066 has not been performed"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:07:42.793311", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:07:32.793311", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0032: MISSING L1B PROCESSING", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_orbpre.py", "op": "=="}
        alerts_l1b_processing = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_l1b_processing) == 1

        assert alerts_l1b_processing[0].message == "The L1B processing for the NOMINAL planned imaging (with timings: 2018-07-20T14:07:32.793311_2018-07-20T14:08:58.407047) over orbit 16066 has not been performed"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:07:42.793311", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:07:32.793311", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0033: MISSING L1C PROCESSING", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_orbpre.py", "op": "=="}
        alerts_l1c_processing = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_l1c_processing) == 1

        assert alerts_l1c_processing[0].message == "The L1C processing for the NOMINAL planned imaging (with timings: 2018-07-20T14:07:32.793311_2018-07-20T14:08:58.407047) over orbit 16066 has not been performed"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L2A", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:07:42.793311", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:07:32.793311", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0034: MISSING L2A PROCESSING", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_orbpre.py", "op": "=="}
        alerts_l2a_processing = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_l2a_processing) == 1

        assert alerts_l2a_processing[0].message == "The L2A processing for the NOMINAL planned imaging (with timings: 2018-07-20T14:07:32.793311_2018-07-20T14:08:58.407047) over orbit 16066 has not been performed"

        if previous_logging_level:
            os.environ["EBOA_LOG_LEVEL"] = previous_logging_level
        else:
            del os.environ["EBOA_LOG_LEVEL"]
        # end if
        
    def test_alerts_orbpre_with_plan_all_operations_last_plan(self):

        previous_logging_level = None
        if "EBOA_LOG_LEVEL" in os.environ:
            previous_logging_level = os.environ["EBOA_LOG_LEVEL"]
        # end if

        # Set log level to INFO to avoid the value get_footprint_command
        os.environ["EBOA_LOG_LEVEL"] = "INFO"
        
        filename = "S2A_ORBPRE_FOR_NPPF_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_NPPF_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check number of alerts generated
        event_alerts = self.query_eboa.get_event_alerts()

        assert len(event_alerts) == 55

        # Check number of alerts generated
        kwargs = {}
        kwargs["gauge_names"] = {"filter": "STATION_SCHEDULE_COMPLETENESS", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:02:47.392053", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-15T14:02:38.392053", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0001: MISSING STATION SCHEDULE", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_nppf.py", "op": "=="}
        alerts_station_schedule = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_station_schedule) == 1

        assert alerts_station_schedule[0].message == "The NOMINAL planned playback (with timings: 2018-07-20T14:02:38.392053_2018-07-20T14:14:20.241401) over orbit 16066 is not covered by any station schedule"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_1", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:02:47.392053", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:02:38.392053", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0010: MISSING PLANNED PLAYBACK CH 1", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_nppf.py", "op": "=="}
        alerts_playback = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_playback) == 1

        assert alerts_playback[0].message == "The NOMINAL planned playback (with timings: 2018-07-20T14:02:38.392053_2018-07-20T14:14:20.241401) over orbit 16066, expected to be received through channel 1, has not been received"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:02:47.392053", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:02:38.392053", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0011: MISSING PLANNED PLAYBACK CH 2", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_nppf.py", "op": "=="}
        alerts_playback = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_playback) == 1

        assert alerts_playback[0].message == "The NOMINAL planned playback (with timings: 2018-07-20T14:02:38.392053_2018-07-20T14:14:20.241401) over orbit 16066, expected to be received through channel 2, has not been received"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:07:42.793311", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:07:32.793311", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0020: MISSING PLANNED IMAGING CH 1", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_nppf.py", "op": "=="}
        alerts_imaging = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_imaging) == 1

        assert alerts_imaging[0].message == "The part of the NOMINAL planned imaging (with timings: 2018-07-20T14:07:32.793311_2018-07-20T14:08:58.407047) over orbit 16066 corresponding to channel 1 has not been received"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_2", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:07:42.793311", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:07:32.793311", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0021: MISSING PLANNED IMAGING CH 2", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_nppf.py", "op": "=="}
        alerts_imaging = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_imaging) == 1

        assert alerts_imaging[0].message == "The part of the NOMINAL planned imaging (with timings: 2018-07-20T14:07:32.793311_2018-07-20T14:08:58.407047) over orbit 16066 corresponding to channel 2 has not been received"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:07:42.793311", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:07:32.793311", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0030: MISSING L0 PROCESSING", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_nppf.py", "op": "=="}
        alerts_l0_processing = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_l0_processing) == 1

        assert alerts_l0_processing[0].message == "The L0 processing for the NOMINAL planned imaging (with timings: 2018-07-20T14:07:32.793311_2018-07-20T14:08:58.407047) over orbit 16066 has not been performed"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1A", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:10:12.951732", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:10:02.951732", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0031: MISSING L1A PROCESSING", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_nppf.py", "op": "=="}
        alerts_l1a_processing = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_l1a_processing) == 1

        assert alerts_l1a_processing[0].message == "The L1A processing for the SUN_CAL planned imaging (with timings: 2018-07-20T14:10:02.951732_2018-07-20T14:16:10.071190) over orbit 16066 has not been performed"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:07:42.793311", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:07:32.793311", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0032: MISSING L1B PROCESSING", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_nppf.py", "op": "=="}
        alerts_l1b_processing = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_l1b_processing) == 1

        assert alerts_l1b_processing[0].message == "The L1B processing for the NOMINAL planned imaging (with timings: 2018-07-20T14:07:32.793311_2018-07-20T14:08:58.407047) over orbit 16066 has not been performed"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:07:42.793311", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:07:32.793311", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0033: MISSING L1C PROCESSING", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_nppf.py", "op": "=="}
        alerts_l1c_processing = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_l1c_processing) == 1

        assert alerts_l1c_processing[0].message == "The L1C processing for the NOMINAL planned imaging (with timings: 2018-07-20T14:07:32.793311_2018-07-20T14:08:58.407047) over orbit 16066 has not been performed"

        kwargs = {}
        kwargs["gauge_names"] = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L2A", "op": "=="}
        kwargs["start_filters"] = [{"date": "2018-07-20T14:07:42.793311", "op": "=="}]
        kwargs["notification_time_filters"] = [{"date": "2018-07-21T00:07:32.793311", "op": "=="}]
        kwargs["names"] = {"filter": "ALERT-0034: MISSING L2A PROCESSING", "op": "=="}
        kwargs["groups"] = {"filter": "S2_PLANNING", "op": "=="}
        kwargs["severities"] = {"filter": "fatal", "op": "=="}
        kwargs["generators"] = {"filter": "ingestion_nppf.py", "op": "=="}
        alerts_l2a_processing = self.query_eboa.get_event_alerts(**kwargs)

        assert len(alerts_l2a_processing) == 1

        assert alerts_l2a_processing[0].message == "The L2A processing for the NOMINAL planned imaging (with timings: 2018-07-20T14:07:32.793311_2018-07-20T14:08:58.407047) over orbit 16066 has not been performed"

        if previous_logging_level:
            os.environ["EBOA_LOG_LEVEL"] = previous_logging_level
        else:
            del os.environ["EBOA_LOG_LEVEL"]
        # end if

    def test_orbpre_with_plan_and_an_empty_plan(self):

        previous_logging_level = None
        if "EBOA_LOG_LEVEL" in os.environ:
            previous_logging_level = os.environ["EBOA_LOG_LEVEL"]
        # end if

        # Set log level to INFO to avoid the value get_footprint_command
        os.environ["EBOA_LOG_LEVEL"] = "INFO"
        
        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_NPPF_EMPTY.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0


        # Check events
        gauges = self.query_eboa.get_gauges(dim_signatures = {"filter": "NPPF_S2A", "op": "=="})
        events = self.query_eboa.get_events(gauge_uuids = {"filter": [gauge.gauge_uuid for gauge in gauges], "op": "in"})

        assert len(events) == 0

        gauges = self.query_eboa.get_gauges(dim_signatures = {"filter": "CORRECTED_NPPF_S2A", "op": "=="})
        events = self.query_eboa.get_events(gauge_uuids = {"filter": [gauge.gauge_uuid for gauge in gauges], "op": "in"})

        assert len(events) == 0


