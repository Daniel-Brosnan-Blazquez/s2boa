"""
Automated tests for the replication of the values of events of the S2BOA submodule

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

class TestS2boaReplicateEventValues(unittest.TestCase):
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

    def test_copy_values_as_they_are(self):

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
             "start": "2018-07-21T10:30:51.776833",
             "stop": "2018-07-21T10:32:51.776833",
             "values": [{"type": "boolean",
                         "name": "BOOLEAN",
                         "value": "True"},
                        {"type": "text",
                         "name": "TEXT",
                         "value": "TEXT"},
                        {"name": "VALUES",
                         "type": "object",
                         "values": [
                             {"type": "text",
                              "name": "TEXT",
                              "value": "TEXT"},
                             {"type": "boolean",
                              "name": "BOOLEAN",
                              "value": "True"},
                             {"type": "boolean",
                              "name": "BOOLEAN2",
                              "value": "false"},
                             {"type": "double",
                              "name": "DOUBLE",
                              "value": "0.9"},
                             {"type": "timestamp",
                              "name": "TIMESTAMP",
                              "value": "20180712T00:00:00"},
                             {"type": "object",
                              "name": "VALUES2",
                              "values": [
                                  {"type": "geometry",
                                   "name": "GEOMETRY",
                                   "value": "-171.455147 -0.281921 -168.925664 0.281908 -168.925664 0.281908 -171.455147 -0.281921"}]
                              }]
                         }]
             }
        ]

        events_with_footprint = s2boa_functions.associate_footprints(events, "S2A")
        
        assert events_with_footprint == [
            {"gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "GAUGE_NAME",
                "system": "GAUGE_SYSTEM"
            },
             "start": "2018-07-21T10:30:51.776833",
             "stop": "2018-07-21T10:32:51.776833",
             "values": [{"type": "boolean",
                         "name": "BOOLEAN",
                         "value": "True"},
                        {"type": "text",
                         "name": "TEXT",
                         "value": "TEXT"},
                        {"name": "VALUES",
                         "type": "object",
                         "values": [
                             {"type": "text",
                              "name": "TEXT",
                              "value": "TEXT"},
                             {"type": "boolean",
                              "name": "BOOLEAN",
                              "value": "True"},
                             {"type": "boolean",
                              "name": "BOOLEAN2",
                              "value": "false"},
                             {"type": "double",
                              "name": "DOUBLE",
                              "value": "0.9"},
                             {"type": "timestamp",
                              "name": "TIMESTAMP",
                              "value": "20180712T00:00:00"},
                             {"type": "object",
                              "name": "VALUES2",
                              "values": [
                                  {"type": "geometry",
                                   "name": "GEOMETRY",
                                   "value": "-171.455147 -0.281921 -168.925664 0.281908 -168.925664 0.281908 -171.455147 -0.281921"}]
                              }]},
                        {"type": "object",
                         "name": "footprint_details",
                         "values": [
                             {"type": "geometry",
                              "name": "footprint",
                              "value": "7.724166 36.15361 7.655237 35.940469 7.586597 35.727294 7.518272 35.514083 7.450259 35.300836 7.382539 35.087556 7.315105 34.874241 7.247972 34.660893 7.181135 34.44751 7.114564 34.234095 7.048278 34.020648 6.982278 33.807167 6.916552 33.593654 6.851083 33.38011 6.785889 33.166534 6.720967 32.952927 6.656294 32.739289 6.591878 32.525621 6.527723 32.311922 6.463825 32.098194 6.400157 31.884436 6.336742 31.670649 6.273577 31.456833 6.210645 31.242988 6.147943 31.029115 6.085482 30.815213 6.023258 30.601284 5.961247 30.387327 5.899465 30.173344 5.837912 29.959333 5.776578 29.745295 5.715451 29.531231 5.654545 29.317141 5.593857 29.103025 2.699492 29.699099 2.75411 29.913818 2.808889 30.128517 2.86383 30.343198 2.918902 30.557862 2.974126 30.772508 3.029519 30.987134 3.085078 31.201741 3.140767 31.416331 3.196632 31.630901 3.252675 31.845451 3.308872 32.059982 3.365228 32.274494 3.42177 32.488985 3.478499 32.703455 3.535371 32.917907 3.592432 33.132338 3.649689 33.346748 3.707126 33.561137 3.764728 33.775506 3.822533 33.989853 3.880545 34.204177 3.938725 34.418482 3.997103 34.632764 4.055695 34.847024 4.114496 35.06126 4.17347 35.275477 4.232667 35.489669 4.29209 35.703838 4.351711 35.917984 4.411538 36.132108 4.4716 36.346207 4.531901 36.560282 4.592387 36.774335 7.724166 36.15361"}]
                         }]
             }
        ]

        data = {"operations": [{
            "mode": "insert",
            "dim_signature": {"name": "dim_signature",
                              "exec": "exec",
                              "version": "1.0"},
            "source": {"name": "source.xml",
                       "reception_time": "2018-06-06T13:33:29",
                       "generation_time": "2018-07-05T02:07:03",
                       "validity_start": "2014-07-05T02:07:03",
                       "validity_stop": "2020-06-05T08:07:36"},
            "events": events_with_footprint
        }]
        }
        exit_status = self.engine_eboa.treat_data(data)

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        events = self.query_eboa.get_events(gauge_names = {"filter": "GAUGE_NAME", "op": "=="},
                                            start_filters = [{"date": "2018-07-21T10:30:51.776833", "op": "=="}],
                                            stop_filters = [{"date": "2018-07-21T10:32:51.776833", "op": "=="}])

        assert len(events) == 1

        geometries = [geometry for geometry in events[0].eventGeometries if geometry.name == "GEOMETRY"]

        assert len(geometries) == 1

        assert geometries[0].to_wkt()["value"] == "POLYGON ((-171.455147 -0.281921, -168.925664 0.281908, -168.925664 0.281908, -171.455147 -0.281921))"

        footprints = [footprint for footprint in events[0].eventGeometries if footprint.name == "footprint"]

        assert len(footprints) == 1

        assert footprints[0].to_wkt()["value"] == "POLYGON ((7.724166 36.15361, 7.655237 35.940469, 7.586597 35.727294, 7.518272 35.514083, 7.450259 35.300836, 7.382539 35.087556, 7.315105 34.874241, 7.247972 34.660893, 7.181135 34.44751, 7.114564 34.234095, 7.048278 34.020648, 6.982278 33.807167, 6.916552 33.593654, 6.851083 33.38011, 6.785889 33.166534, 6.720967 32.952927, 6.656294 32.739289, 6.591878 32.525621, 6.527723 32.311922, 6.463825 32.098194, 6.400157 31.884436, 6.336742 31.670649, 6.273577 31.456833, 6.210645 31.242988, 6.147943 31.029115, 6.085482 30.815213, 6.023258 30.601284, 5.961247 30.387327, 5.899465 30.173344, 5.837912 29.959333, 5.776578 29.745295, 5.715451 29.531231, 5.654545 29.317141, 5.593857 29.103025, 2.699492 29.699099, 2.75411 29.913818, 2.808889 30.128517, 2.86383 30.343198, 2.918902 30.557862, 2.974126 30.772508, 3.029519 30.987134, 3.085078 31.201741, 3.140767 31.416331, 3.196632 31.630901, 3.252675 31.845451, 3.308872 32.059982, 3.365228 32.274494, 3.42177 32.488985, 3.478499 32.703455, 3.535371 32.917907, 3.592432 33.132338, 3.649689 33.346748, 3.707126 33.561137, 3.764728 33.775506, 3.822533 33.989853, 3.880545 34.204177, 3.938725 34.418482, 3.997103 34.632764, 4.055695 34.847024, 4.114496 35.06126, 4.17347 35.275477, 4.232667 35.489669, 4.29209 35.703838, 4.351711 35.917984, 4.411538 36.132108, 4.4716 36.346207, 4.531901 36.560282, 4.592387 36.774335, 7.724166 36.15361))"

        data = {"operations": [{
            "mode": "insert_and_erase",
            "dim_signature": {"name": "dim_signature",
                              "exec": "exec",
                              "version": "1.0"},
            "source": {"name": "source1.xml",
                       "reception_time": "2018-06-06T13:33:29",
                       "generation_time": "2020-07-05T02:07:03",
                       "validity_start": "2014-07-05T02:07:03",
                       "validity_stop": "2018-07-21T10:31:30"}
        }]
        }

        exit_status = self.engine_eboa.treat_data(data)

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        events = self.query_eboa.get_events(gauge_names = {"filter": "GAUGE_NAME", "op": "=="},
                                            start_filters = [{"date": "2018-07-21T10:31:30", "op": "=="}],
                                            stop_filters = [{"date": "2018-07-21T10:32:51.776833", "op": "=="}])

        assert len(events) == 1

        assert events[0].get_structured_values() == [
            {"type": "boolean",
             "name": "BOOLEAN",
             "value": "True"},
            {"type": "text",
             "name": "TEXT",
             "value": "TEXT"},
            {"name": "VALUES",
             "type": "object",
             "values": [
                 {"type": "text",
                  "name": "TEXT",
                  "value": "TEXT"},
                 {"type": "boolean",
                  "name": "BOOLEAN",
                  "value": "True"},
                 {"type": "boolean",
                  "name": "BOOLEAN2",
                  "value": "False"},
                 {"type": "double",
                  "name": "DOUBLE",
                  "value": "0.9"},
                 {"type": "timestamp",
                  "name": "TIMESTAMP",
                  "value": "2018-07-12T00:00:00"},
                 {"type": "object",
                  "name": "VALUES2",
                  "values": [
                      {"type": "geometry",
                       "name": "GEOMETRY",
                       "value": "POLYGON ((-171.455147 -0.281921, -168.925664 0.281908, -168.925664 0.281908, -171.455147 -0.281921))"}]
                  }]},
            {"type": "object",
             "name": "footprint_details",
             "values": [
                 {"type": "geometry",
                  "name": "footprint",
                  "value": "POLYGON ((7.724166 36.15361, 7.655237 35.940469, 7.586597 35.727294, 7.518272 35.514083, 7.450259 35.300836, 7.382539 35.087556, 7.315105 34.874241, 7.247972 34.660893, 7.181135 34.44751, 7.114564 34.234095, 7.048278 34.020648, 6.982278 33.807167, 6.916552 33.593654, 6.851083 33.38011, 6.785889 33.166534, 6.720967 32.952927, 6.656294 32.739289, 6.591878 32.525621, 6.527723 32.311922, 6.463825 32.098194, 6.400157 31.884436, 6.336742 31.670649, 6.273577 31.456833, 6.210645 31.242988, 6.147943 31.029115, 6.085482 30.815213, 6.023258 30.601284, 5.961247 30.387327, 5.899465 30.173344, 5.837912 29.959333, 5.776578 29.745295, 5.715451 29.531231, 5.654545 29.317141, 5.593857 29.103025, 2.699492 29.699099, 2.75411 29.913818, 2.808889 30.128517, 2.86383 30.343198, 2.918902 30.557862, 2.974126 30.772508, 3.029519 30.987134, 3.085078 31.201741, 3.140767 31.416331, 3.196632 31.630901, 3.252675 31.845451, 3.308872 32.059982, 3.365228 32.274494, 3.42177 32.488985, 3.478499 32.703455, 3.535371 32.917907, 3.592432 33.132338, 3.649689 33.346748, 3.707126 33.561137, 3.764728 33.775506, 3.822533 33.989853, 3.880545 34.204177, 3.938725 34.418482, 3.997103 34.632764, 4.055695 34.847024, 4.114496 35.06126, 4.17347 35.275477, 4.232667 35.489669, 4.29209 35.703838, 4.351711 35.917984, 4.411538 36.132108, 4.4716 36.346207, 4.531901 36.560282, 4.592387 36.774335, 7.724166 36.15361))"}]
             }]

    def test_update_footprint_using_satellite(self):

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
             "start": "2018-07-21T10:30:51.776833",
             "stop": "2018-07-21T10:32:51.776833",
             "values": [{"type": "boolean",
                         "name": "BOOLEAN",
                         "value": "True"},
                        {"type": "text",
                         "name": "TEXT",
                         "value": "TEXT"},
                        {"name": "VALUES",
                         "type": "object",
                         "values": [
                             {"type": "text",
                              "name": "satellite",
                              "value": "S2A"},
                             {"type": "boolean",
                              "name": "BOOLEAN",
                              "value": "True"},
                             {"type": "boolean",
                              "name": "BOOLEAN2",
                              "value": "false"},
                             {"type": "double",
                              "name": "DOUBLE",
                              "value": "0.9"},
                             {"type": "timestamp",
                              "name": "TIMESTAMP",
                              "value": "20180712T00:00:00"},
                             {"type": "object",
                              "name": "VALUES2",
                              "values": [
                                  {"type": "geometry",
                                   "name": "GEOMETRY",
                                   "value": "-171.455147 -0.281921 -168.925664 0.281908 -168.925664 0.281908 -171.455147 -0.281921"}]
                              }]
                         }]
             }
        ]

        events_with_footprint = s2boa_functions.associate_footprints(events, "S2A")
        
        assert events_with_footprint == [
            {"gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "GAUGE_NAME",
                "system": "GAUGE_SYSTEM"
            },
             "start": "2018-07-21T10:30:51.776833",
             "stop": "2018-07-21T10:32:51.776833",
             "values": [{"type": "boolean",
                         "name": "BOOLEAN",
                         "value": "True"},
                        {"type": "text",
                         "name": "TEXT",
                         "value": "TEXT"},
                        {"name": "VALUES",
                         "type": "object",
                         "values": [
                             {"type": "text",
                              "name": "satellite",
                              "value": "S2A"},
                             {"type": "boolean",
                              "name": "BOOLEAN",
                              "value": "True"},
                             {"type": "boolean",
                              "name": "BOOLEAN2",
                              "value": "false"},
                             {"type": "double",
                              "name": "DOUBLE",
                              "value": "0.9"},
                             {"type": "timestamp",
                              "name": "TIMESTAMP",
                              "value": "20180712T00:00:00"},
                             {"type": "object",
                              "name": "VALUES2",
                              "values": [
                                  {"type": "geometry",
                                   "name": "GEOMETRY",
                                   "value": "-171.455147 -0.281921 -168.925664 0.281908 -168.925664 0.281908 -171.455147 -0.281921"}]
                              }]},
                        {"type": "object",
                         "name": "footprint_details",
                         "values": [
                             {"type": "geometry",
                              "name": "footprint",
                              "value": "7.724166 36.15361 7.655237 35.940469 7.586597 35.727294 7.518272 35.514083 7.450259 35.300836 7.382539 35.087556 7.315105 34.874241 7.247972 34.660893 7.181135 34.44751 7.114564 34.234095 7.048278 34.020648 6.982278 33.807167 6.916552 33.593654 6.851083 33.38011 6.785889 33.166534 6.720967 32.952927 6.656294 32.739289 6.591878 32.525621 6.527723 32.311922 6.463825 32.098194 6.400157 31.884436 6.336742 31.670649 6.273577 31.456833 6.210645 31.242988 6.147943 31.029115 6.085482 30.815213 6.023258 30.601284 5.961247 30.387327 5.899465 30.173344 5.837912 29.959333 5.776578 29.745295 5.715451 29.531231 5.654545 29.317141 5.593857 29.103025 2.699492 29.699099 2.75411 29.913818 2.808889 30.128517 2.86383 30.343198 2.918902 30.557862 2.974126 30.772508 3.029519 30.987134 3.085078 31.201741 3.140767 31.416331 3.196632 31.630901 3.252675 31.845451 3.308872 32.059982 3.365228 32.274494 3.42177 32.488985 3.478499 32.703455 3.535371 32.917907 3.592432 33.132338 3.649689 33.346748 3.707126 33.561137 3.764728 33.775506 3.822533 33.989853 3.880545 34.204177 3.938725 34.418482 3.997103 34.632764 4.055695 34.847024 4.114496 35.06126 4.17347 35.275477 4.232667 35.489669 4.29209 35.703838 4.351711 35.917984 4.411538 36.132108 4.4716 36.346207 4.531901 36.560282 4.592387 36.774335 7.724166 36.15361"}]
                         }]
             }
        ]

        data = {"operations": [{
            "mode": "insert",
            "dim_signature": {"name": "dim_signature",
                              "exec": "exec",
                              "version": "1.0"},
            "source": {"name": "source.xml",
                       "reception_time": "2018-06-06T13:33:29",
                       "generation_time": "2018-07-05T02:07:03",
                       "validity_start": "2014-07-05T02:07:03",
                       "validity_stop": "2020-06-05T08:07:36"},
            "events": events_with_footprint
        }]
        }
        exit_status = self.engine_eboa.treat_data(data)

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        events = self.query_eboa.get_events(gauge_names = {"filter": "GAUGE_NAME", "op": "=="},
                                            start_filters = [{"date": "2018-07-21T10:30:51.776833", "op": "=="}],
                                            stop_filters = [{"date": "2018-07-21T10:32:51.776833", "op": "=="}])

        assert len(events) == 1

        geometries = [geometry for geometry in events[0].eventGeometries if geometry.name == "GEOMETRY"]

        assert len(geometries) == 1

        assert geometries[0].to_wkt()["value"] == "POLYGON ((-171.455147 -0.281921, -168.925664 0.281908, -168.925664 0.281908, -171.455147 -0.281921))"

        footprints = [footprint for footprint in events[0].eventGeometries if footprint.name == "footprint"]

        assert len(footprints) == 1

        assert footprints[0].to_wkt()["value"] == "POLYGON ((7.724166 36.15361, 7.655237 35.940469, 7.586597 35.727294, 7.518272 35.514083, 7.450259 35.300836, 7.382539 35.087556, 7.315105 34.874241, 7.247972 34.660893, 7.181135 34.44751, 7.114564 34.234095, 7.048278 34.020648, 6.982278 33.807167, 6.916552 33.593654, 6.851083 33.38011, 6.785889 33.166534, 6.720967 32.952927, 6.656294 32.739289, 6.591878 32.525621, 6.527723 32.311922, 6.463825 32.098194, 6.400157 31.884436, 6.336742 31.670649, 6.273577 31.456833, 6.210645 31.242988, 6.147943 31.029115, 6.085482 30.815213, 6.023258 30.601284, 5.961247 30.387327, 5.899465 30.173344, 5.837912 29.959333, 5.776578 29.745295, 5.715451 29.531231, 5.654545 29.317141, 5.593857 29.103025, 2.699492 29.699099, 2.75411 29.913818, 2.808889 30.128517, 2.86383 30.343198, 2.918902 30.557862, 2.974126 30.772508, 3.029519 30.987134, 3.085078 31.201741, 3.140767 31.416331, 3.196632 31.630901, 3.252675 31.845451, 3.308872 32.059982, 3.365228 32.274494, 3.42177 32.488985, 3.478499 32.703455, 3.535371 32.917907, 3.592432 33.132338, 3.649689 33.346748, 3.707126 33.561137, 3.764728 33.775506, 3.822533 33.989853, 3.880545 34.204177, 3.938725 34.418482, 3.997103 34.632764, 4.055695 34.847024, 4.114496 35.06126, 4.17347 35.275477, 4.232667 35.489669, 4.29209 35.703838, 4.351711 35.917984, 4.411538 36.132108, 4.4716 36.346207, 4.531901 36.560282, 4.592387 36.774335, 7.724166 36.15361))"

        data = {"operations": [{
            "mode": "insert_and_erase",
            "dim_signature": {"name": "dim_signature",
                              "exec": "exec",
                              "version": "1.0"},
            "source": {"name": "source1.xml",
                       "reception_time": "2018-06-06T13:33:29",
                       "generation_time": "2020-07-05T02:07:03",
                       "validity_start": "2014-07-05T02:07:03",
                       "validity_stop": "2018-07-21T10:31:30"}
        }]
        }

        exit_status = self.engine_eboa.treat_data(data)

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        events = self.query_eboa.get_events(gauge_names = {"filter": "GAUGE_NAME", "op": "=="},
                                            start_filters = [{"date": "2018-07-21T10:31:30", "op": "=="}],
                                            stop_filters = [{"date": "2018-07-21T10:32:51.776833", "op": "=="}])

        assert len(events) == 1

        assert events[0].get_structured_values() == [
            {"type": "boolean",
             "name": "BOOLEAN",
             "value": "True"},
            {"type": "text",
             "name": "TEXT",
             "value": "TEXT"},
            {"name": "VALUES",
             "type": "object",
             "values": [
                 {"type": "text",
                  "name": "satellite",
                  "value": "S2A"},
                 {"type": "boolean",
                  "name": "BOOLEAN",
                  "value": "True"},
                 {"type": "boolean",
                  "name": "BOOLEAN2",
                  "value": "False"},
                 {"type": "double",
                  "name": "DOUBLE",
                  "value": "0.9"},
                 {"type": "timestamp",
                  "name": "TIMESTAMP",
                  "value": "2018-07-12T00:00:00"},
                 {"type": "object",
                  "name": "VALUES2",
                  "values": [
                      {"type": "geometry",
                       "name": "GEOMETRY",
                       "value": "POLYGON ((-171.455147 -0.281921, -168.925664 0.281908, -168.925664 0.281908, -171.455147 -0.281921))"}]
                  }]},
            {"type": "object",
             "name": "footprint_details_0",
             "values": [
                 {"type": "geometry",
                  "name": "footprint",
                  "value": "POLYGON ((7.014498 33.911484, 6.947167 33.693245, 6.880128 33.474972, 6.813377 33.256666, 6.74689 33.038328, 6.680677 32.819958, 6.614741 32.601555, 6.549078 32.38312, 6.483661 32.164655, 6.41851 31.946159, 6.353623 31.727631, 6.288992 31.509073, 6.224598 31.290486, 6.160457 31.071869, 6.096567 30.853222, 6.032916 30.634546, 5.969495 30.415842, 5.906315 30.197108, 5.843374 29.978347, 5.780657 29.759558, 5.718161 29.540741, 5.655896 29.321897, 5.593857 29.103025, 2.699492 29.699099, 2.755326 29.918586, 2.811325 30.138054, 2.867492 30.357502, 2.923806 30.576932, 2.98027 30.796343, 3.036909 31.015735, 3.093724 31.235105, 3.150688 31.454457, 3.207819 31.67379, 3.265134 31.893101, 3.322636 32.112391, 3.380287 32.331663, 3.438123 32.550913, 3.496154 32.770141, 3.55438 32.989348, 3.61276 33.208535, 3.671342 33.427699, 3.73013 33.646841, 3.789115 33.865961, 3.848273 34.08506, 3.907644 34.304136, 3.967234 34.523189, 7.014498 33.911484))"}]
             }]

    def test_update_footprint_using_satellite_antimeridian(self):

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
             "start": "2018-07-21T10:00:00",
             "stop": "2018-07-21T10:04:00",
             "values": [{"type": "boolean",
                         "name": "BOOLEAN",
                         "value": "True"},
                        {"type": "text",
                         "name": "TEXT",
                         "value": "TEXT"},
                        {"name": "VALUES",
                         "type": "object",
                         "values": [
                             {"type": "text",
                              "name": "satellite",
                              "value": "S2A"},
                             {"type": "boolean",
                              "name": "BOOLEAN",
                              "value": "True"},
                             {"type": "boolean",
                              "name": "BOOLEAN2",
                              "value": "false"},
                             {"type": "double",
                              "name": "DOUBLE",
                              "value": "0.9"},
                             {"type": "timestamp",
                              "name": "TIMESTAMP",
                              "value": "20180712T00:00:00"},
                             {"type": "object",
                              "name": "VALUES2",
                              "values": [
                                  {"type": "geometry",
                                   "name": "GEOMETRY",
                                   "value": "-171.455147 -0.281921 -168.925664 0.281908 -168.925664 0.281908 -171.455147 -0.281921"}]
                              }]
                         }]
             }
        ]

        events_with_footprint = s2boa_functions.associate_footprints(events, "S2A")
        
        data = {"operations": [{
            "mode": "insert",
            "dim_signature": {"name": "dim_signature",
                              "exec": "exec",
                              "version": "1.0"},
            "source": {"name": "source.xml",
                       "reception_time": "2018-06-06T13:33:29",
                       "generation_time": "2018-07-05T02:07:03",
                       "validity_start": "2014-07-05T02:07:03",
                       "validity_stop": "2020-06-05T08:07:36"},
            "events": events_with_footprint
        }]
        }
        exit_status = self.engine_eboa.treat_data(data)

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        assert events_with_footprint == [
            {"gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "GAUGE_NAME",
                "system": "GAUGE_SYSTEM"
            },
             "start": "2018-07-21T10:00:00",
             "stop": "2018-07-21T10:04:00",
             "values": [{"type": "boolean",
                         "name": "BOOLEAN",
                         "value": "True"},
                        {"type": "text",
                         "name": "TEXT",
                         "value": "TEXT"},
                        {"name": "VALUES",
                         "type": "object",
                         "values": [
                             {"type": "text",
                              "name": "satellite",
                              "value": "S2A"},
                             {"type": "boolean",
                              "name": "BOOLEAN",
                              "value": "True"},
                             {"type": "boolean",
                              "name": "BOOLEAN2",
                              "value": "false"},
                             {"type": "double",
                              "name": "DOUBLE",
                              "value": "0.9"},
                             {"type": "timestamp",
                              "name": "TIMESTAMP",
                              "value": "20180712T00:00:00"},
                             {"type": "object",
                              "name": "VALUES2",
                              "values": [
                                  {"type": "geometry",
                                   "name": "GEOMETRY",
                                   "value": "-171.455147 -0.281921 -168.925664 0.281908 -168.925664 0.281908 -171.455147 -0.281921"}]
                              }]},
                        {"type": "object",
                         "name": "footprint_details_0",
                         "values": [
                             {"type": "geometry",
                              "name": "footprint",
                              "value": "-179.427364 32.145203 -179.491322 32.358931 -179.555539 32.572629 -179.620015 32.786296 -179.684733 32.999933 -179.74972 33.213539 -179.81498 33.427113 -179.880499 33.640656 -179.946285 33.854168 -180.0 34.027729344730545 -180.0 44.75671719951115 -179.988292 44.722094 -179.916675 44.50912 -179.845461 44.296111 -179.774635 44.083066 -179.704137 43.86999 -179.634025 43.656879 -179.564295 43.443734 -179.4949 43.230556 -179.425843 43.017347 -179.357151 42.804105 -179.288819 42.590829 -179.220775 42.377525 -179.153078 42.164188 -179.085726 41.950819 -179.018688 41.737419 -178.951943 41.523991 -178.885529 41.310532 -178.819441 41.097041 -178.753624 40.883523 -178.688108 40.669976 -178.622906 40.456399 -178.558001 40.242793 -178.493346 40.02916 -178.428993 39.815499 -178.364935 39.601808 -178.301133 39.388091 -178.237593 39.174348 -178.174337 38.960576 -178.111362 38.746776 -178.048602 38.532953 -177.986116 38.319103 -177.923898 38.105225 -177.861923 37.891322 -177.800173 37.677395 -177.738682 37.463441 -177.677447 37.249462 -177.616416 37.03546 -177.555622 36.821432 -177.495074 36.60738 -177.434756 36.393303 -177.374631 36.179204 -177.314742 35.965081 -177.255085 35.750933 -177.195623 35.536763 -177.136367 35.32257 -177.077334 35.108354 -177.018521 34.894115 -176.959871 34.679855 -176.901436 34.465572 -176.843214 34.251267 -176.785178 34.03694 -176.727317 33.822593 -176.669661 33.608223 -176.612206 33.393832 -176.554905 33.179421 -176.497792 32.964989 -176.440872 32.750536 -179.427364 32.145203"}]
                         },
                        {"type": "object",
                         "name": "footprint_details_1",
                         "values": [
                             {"type": "geometry",
                              "name": "footprint",
                              "value": "180.0 34.027729344730545 179.987646 34.067647 179.921292 34.281093 179.854676 34.494507 179.787768 34.707887 179.720563 34.921234 179.653069 35.134546 179.585289 35.347825 179.517202 35.561069 179.448802 35.774278 179.38011 35.987452 179.311106 36.20059 179.241778 36.413691 179.172127 36.626756 179.102171 36.839785 179.031878 37.052776 178.961244 37.265729 178.890285 37.478644 178.81899 37.691522 178.747341 37.904359 178.675333 38.117157 178.602997 38.329917 178.530292 38.542636 178.457215 38.755314 178.383775 38.96795 178.309973 39.180547 178.235784 39.3931 178.161202 39.605611 178.086253 39.81808 178.010908 40.030505 177.935153 40.242886 177.858994 40.455222 177.782446 40.667515 177.705472 40.879762 177.628068 41.091962 177.550253 41.304117 177.47201 41.516225 177.393318 41.728285 177.314174 41.940296 177.234609 42.152262 177.154578 42.364177 177.074073 42.576041 176.993108 42.787856 176.91168 42.999621 176.829759 43.211334 176.747338 43.422994 176.664449 43.634603 176.581052 43.846159 176.497134 44.057659 176.4127 44.269105 176.327764 44.480498 176.242285 44.691834 176.156255 44.903112 176.069697 45.114335 175.982589 45.325499 175.894906 45.536605 175.806643 45.74765 175.717834 45.958637 175.628425 46.169563 179.273307 46.849842 179.349067 46.637237 179.424361 46.42459 179.499266 46.21191 179.573725 45.99919 179.647736 45.786431 179.721333 45.573636 179.794548 45.360805 179.867336 45.147938 179.939702 44.935032 180.0 44.75671719951115 180.0 34.027729344730545"}]
                         }]
             }
        ]
        
        events = self.query_eboa.get_events(gauge_names = {"filter": "GAUGE_NAME", "op": "=="},
                                            start_filters = [{"date": "2018-07-21T10:00:00", "op": "=="}],
                                            stop_filters = [{"date": "2018-07-21T10:04:00", "op": "=="}])

        assert len(events) == 1

        geometries = [geometry for geometry in events[0].eventGeometries if geometry.name == "GEOMETRY"]

        assert len(geometries) == 1

        assert geometries[0].to_wkt()["value"] == "POLYGON ((-171.455147 -0.281921, -168.925664 0.281908, -168.925664 0.281908, -171.455147 -0.281921))"

        footprints = [footprint for footprint in events[0].eventGeometries if footprint.name == "footprint"]
        footprints.sort(key=lambda x: x.parent_position)

        assert len(footprints) == 2

        assert footprints[0].to_wkt()["value"] == "POLYGON ((-179.427364 32.145203, -179.491322 32.358931, -179.555539 32.572629, -179.620015 32.786296, -179.684733 32.999933, -179.74972 33.213539, -179.81498 33.427113, -179.880499 33.640656, -179.946285 33.854168, -180 34.02772934473055, -180 44.75671719951115, -179.988292 44.722094, -179.916675 44.50912, -179.845461 44.296111, -179.774635 44.083066, -179.704137 43.86999, -179.634025 43.656879, -179.564295 43.443734, -179.4949 43.230556, -179.425843 43.017347, -179.357151 42.804105, -179.288819 42.590829, -179.220775 42.377525, -179.153078 42.164188, -179.085726 41.950819, -179.018688 41.737419, -178.951943 41.523991, -178.885529 41.310532, -178.819441 41.097041, -178.753624 40.883523, -178.688108 40.669976, -178.622906 40.456399, -178.558001 40.242793, -178.493346 40.02916, -178.428993 39.815499, -178.364935 39.601808, -178.301133 39.388091, -178.237593 39.174348, -178.174337 38.960576, -178.111362 38.746776, -178.048602 38.532953, -177.986116 38.319103, -177.923898 38.105225, -177.861923 37.891322, -177.800173 37.677395, -177.738682 37.463441, -177.677447 37.249462, -177.616416 37.03546, -177.555622 36.821432, -177.495074 36.60738, -177.434756 36.393303, -177.374631 36.179204, -177.314742 35.965081, -177.255085 35.750933, -177.195623 35.536763, -177.136367 35.32257, -177.077334 35.108354, -177.018521 34.894115, -176.959871 34.679855, -176.901436 34.465572, -176.843214 34.251267, -176.785178 34.03694, -176.727317 33.822593, -176.669661 33.608223, -176.612206 33.393832, -176.554905 33.179421, -176.497792 32.964989, -176.440872 32.750536, -179.427364 32.145203))"

        assert footprints[1].to_wkt()["value"] == "POLYGON ((180 34.02772934473055, 179.987646 34.067647, 179.921292 34.281093, 179.854676 34.494507, 179.787768 34.707887, 179.720563 34.921234, 179.653069 35.134546, 179.585289 35.347825, 179.517202 35.561069, 179.448802 35.774278, 179.38011 35.987452, 179.311106 36.20059, 179.241778 36.413691, 179.172127 36.626756, 179.102171 36.839785, 179.031878 37.052776, 178.961244 37.265729, 178.890285 37.478644, 178.81899 37.691522, 178.747341 37.904359, 178.675333 38.117157, 178.602997 38.329917, 178.530292 38.542636, 178.457215 38.755314, 178.383775 38.96795, 178.309973 39.180547, 178.235784 39.3931, 178.161202 39.605611, 178.086253 39.81808, 178.010908 40.030505, 177.935153 40.242886, 177.858994 40.455222, 177.782446 40.667515, 177.705472 40.879762, 177.628068 41.091962, 177.550253 41.304117, 177.47201 41.516225, 177.393318 41.728285, 177.314174 41.940296, 177.234609 42.152262, 177.154578 42.364177, 177.074073 42.576041, 176.993108 42.787856, 176.91168 42.999621, 176.829759 43.211334, 176.747338 43.422994, 176.664449 43.634603, 176.581052 43.846159, 176.497134 44.057659, 176.4127 44.269105, 176.327764 44.480498, 176.242285 44.691834, 176.156255 44.903112, 176.069697 45.114335, 175.982589 45.325499, 175.894906 45.536605, 175.806643 45.74765, 175.717834 45.958637, 175.628425 46.169563, 179.273307 46.849842, 179.349067 46.637237, 179.424361 46.42459, 179.499266 46.21191, 179.573725 45.99919, 179.647736 45.786431, 179.721333 45.573636, 179.794548 45.360805, 179.867336 45.147938, 179.939702 44.935032, 180 44.75671719951115, 180 34.02772934473055))"

        data = {"operations": [{
            "mode": "insert_and_erase",
            "dim_signature": {"name": "dim_signature",
                              "exec": "exec",
                              "version": "1.0"},
            "source": {"name": "source1.xml",
                       "reception_time": "2018-06-06T13:33:29",
                       "generation_time": "2020-07-05T02:07:03",
                       "validity_start": "2014-07-05T02:07:03",
                       "validity_stop": "2018-07-21T10:01:00"}
        }]
        }

        exit_status = self.engine_eboa.treat_data(data)

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        events = self.query_eboa.get_events(gauge_names = {"filter": "GAUGE_NAME", "op": "=="},
                                            start_filters = [{"date": "2018-07-21T10:01:00", "op": "=="}],
                                            stop_filters = [{"date": "2018-07-21T10:04:00", "op": "=="}])

        assert len(events) == 1

        assert events[0].get_structured_values() == [
            {"type": "boolean",
             "name": "BOOLEAN",
             "value": "True"},
            {"type": "text",
             "name": "TEXT",
             "value": "TEXT"},
            {"name": "VALUES",
             "type": "object",
             "values": [
                 {"type": "text",
                  "name": "satellite",
                  "value": "S2A"},
                 {"type": "boolean",
                  "name": "BOOLEAN",
                  "value": "True"},
                 {"type": "boolean",
                  "name": "BOOLEAN2",
                  "value": "False"},
                 {"type": "double",
                  "name": "DOUBLE",
                  "value": "0.9"},
                 {"type": "timestamp",
                  "name": "TIMESTAMP",
                  "value": "2018-07-12T00:00:00"},
                 {"type": "object",
                  "name": "VALUES2",
                  "values": [
                      {"type": "geometry",
                       "name": "GEOMETRY",
                       "value": "POLYGON ((-171.455147 -0.281921, -168.925664 0.281908, -168.925664 0.281908, -171.455147 -0.281921))"}]
                  }]},
            {"type": "object",
             "name": "footprint_details_0",
             "values": [
                 {"type": "geometry",
                  "name": "footprint",
                  "value": "POLYGON ((-180 35.77042462822262, -180 44.75666858978662, -179.980974 44.700363, -179.908663 44.485213, -179.836761 44.270026, -179.765262 44.054803, -179.694105 43.839547, -179.623325 43.624257, -179.552931 43.408932, -179.482912 43.193572, -179.413204 42.978183, -179.343867 42.762759, -179.274895 42.547301, -179.206254 42.331811, -179.137928 42.116291, -179.069952 41.900739, -179.00232 41.685154, -178.934981 41.469539, -178.867958 41.253895, -178.801265 41.038219, -178.734897 40.822512, -178.668786 40.606778, -178.602993 40.391013, -178.537513 40.175219, -178.472319 39.959395, -178.407387 39.743545, -178.342755 39.527665, -178.278419 39.311757, -178.214335 39.095822, -178.150517 38.87986, -178.086982 38.663869, -178.023728 38.447851, -177.960692 38.231809, -177.897926 38.015739, -177.835428 37.799642, -177.77318 37.583519, -177.711151 37.367373, -177.64938 37.1512, -177.587863 36.935, -177.526564 36.718777, -177.465489 36.50253, -177.404658 36.286257, -180 35.77042462822262))"
                  }]},
            {"type": "object",
             "name": "footprint_details_1",
             "values": [
                 {"type": "geometry",
                  "name": "footprint",
                  "value": "POLYGON ((180 35.77042462822262, 179.483044 35.667678, 179.413801 35.883045, 179.344234 36.098375, 179.274353 36.313668, 179.204157 36.528925, 179.133625 36.744144, 179.062751 36.959325, 178.991556 37.174468, 178.920021 37.389573, 178.848131 37.604638, 178.775883 37.819663, 178.703304 38.034649, 178.630357 38.249595, 178.557036 38.464499, 178.48335 38.679362, 178.409304 38.894184, 178.334869 39.108963, 178.260041 39.323699, 178.184839 39.538393, 178.109246 39.753043, 178.033243 39.967649, 177.956825 40.182209, 177.880025 40.396726, 177.802799 40.611197, 177.725143 40.825621, 177.647059 41.039998, 177.568561 41.25433, 177.489613 41.468613, 177.41021 41.682847, 177.330369 41.897033, 177.250076 42.111171, 177.16931 42.325257, 177.088062 42.539292, 177.006364 42.753278, 176.924177 42.967212, 176.841488 43.181092, 176.758299 43.394919, 176.67463 43.608695, 176.590438 43.822415, 176.505716 44.03608, 176.42048 44.249689, 176.33472 44.463244, 176.248407 44.67674, 176.161533 44.890178, 176.074129 45.10356, 175.986156 45.316882, 175.897597 45.530143, 175.808451 45.743343, 175.718743 45.956485, 175.628425 46.169563, 179.273307 46.849842, 179.349838 46.635067, 179.425895 46.420251, 179.50155 46.205398, 179.576754 45.990507, 179.651505 45.775575, 179.725821 45.560606, 179.799758 45.345602, 179.873262 45.130559, 179.946337 44.915479, 180 44.75666858978662, 180 35.77042462822262))"}]
             }]

    def test_update_footprint_using_satellite_antimeridian_no_other_values(self):

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
             "start": "2018-07-21T10:00:00",
             "stop": "2018-07-21T10:04:00",
             "values": [{"type": "text",
                         "name": "satellite",
                         "value": "S2A"}]
             }
        ]

        events_with_footprint = s2boa_functions.associate_footprints(events, "S2A")
        
        data = {"operations": [{
            "mode": "insert",
            "dim_signature": {"name": "dim_signature",
                              "exec": "exec",
                              "version": "1.0"},
            "source": {"name": "source.xml",
                       "reception_time": "2018-06-06T13:33:29",
                       "generation_time": "2018-07-05T02:07:03",
                       "validity_start": "2014-07-05T02:07:03",
                       "validity_stop": "2020-06-05T08:07:36"},
            "events": events_with_footprint
        }]
        }
        exit_status = self.engine_eboa.treat_data(data)

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        assert events_with_footprint == [
            {"gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "GAUGE_NAME",
                "system": "GAUGE_SYSTEM"
            },
             "start": "2018-07-21T10:00:00",
             "stop": "2018-07-21T10:04:00",
             "values": [{"type": "text",
                         "name": "satellite",
                         "value": "S2A"},
                        {"type": "object",
                         "name": "footprint_details_0",
                         "values": [
                             {"type": "geometry",
                              "name": "footprint",
                              "value": "-179.427364 32.145203 -179.491322 32.358931 -179.555539 32.572629 -179.620015 32.786296 -179.684733 32.999933 -179.74972 33.213539 -179.81498 33.427113 -179.880499 33.640656 -179.946285 33.854168 -180.0 34.027729344730545 -180.0 44.75671719951115 -179.988292 44.722094 -179.916675 44.50912 -179.845461 44.296111 -179.774635 44.083066 -179.704137 43.86999 -179.634025 43.656879 -179.564295 43.443734 -179.4949 43.230556 -179.425843 43.017347 -179.357151 42.804105 -179.288819 42.590829 -179.220775 42.377525 -179.153078 42.164188 -179.085726 41.950819 -179.018688 41.737419 -178.951943 41.523991 -178.885529 41.310532 -178.819441 41.097041 -178.753624 40.883523 -178.688108 40.669976 -178.622906 40.456399 -178.558001 40.242793 -178.493346 40.02916 -178.428993 39.815499 -178.364935 39.601808 -178.301133 39.388091 -178.237593 39.174348 -178.174337 38.960576 -178.111362 38.746776 -178.048602 38.532953 -177.986116 38.319103 -177.923898 38.105225 -177.861923 37.891322 -177.800173 37.677395 -177.738682 37.463441 -177.677447 37.249462 -177.616416 37.03546 -177.555622 36.821432 -177.495074 36.60738 -177.434756 36.393303 -177.374631 36.179204 -177.314742 35.965081 -177.255085 35.750933 -177.195623 35.536763 -177.136367 35.32257 -177.077334 35.108354 -177.018521 34.894115 -176.959871 34.679855 -176.901436 34.465572 -176.843214 34.251267 -176.785178 34.03694 -176.727317 33.822593 -176.669661 33.608223 -176.612206 33.393832 -176.554905 33.179421 -176.497792 32.964989 -176.440872 32.750536 -179.427364 32.145203"}]
                         },
                        {"type": "object",
                         "name": "footprint_details_1",
                         "values": [
                             {"type": "geometry",
                              "name": "footprint",
                              "value": "180.0 34.027729344730545 179.987646 34.067647 179.921292 34.281093 179.854676 34.494507 179.787768 34.707887 179.720563 34.921234 179.653069 35.134546 179.585289 35.347825 179.517202 35.561069 179.448802 35.774278 179.38011 35.987452 179.311106 36.20059 179.241778 36.413691 179.172127 36.626756 179.102171 36.839785 179.031878 37.052776 178.961244 37.265729 178.890285 37.478644 178.81899 37.691522 178.747341 37.904359 178.675333 38.117157 178.602997 38.329917 178.530292 38.542636 178.457215 38.755314 178.383775 38.96795 178.309973 39.180547 178.235784 39.3931 178.161202 39.605611 178.086253 39.81808 178.010908 40.030505 177.935153 40.242886 177.858994 40.455222 177.782446 40.667515 177.705472 40.879762 177.628068 41.091962 177.550253 41.304117 177.47201 41.516225 177.393318 41.728285 177.314174 41.940296 177.234609 42.152262 177.154578 42.364177 177.074073 42.576041 176.993108 42.787856 176.91168 42.999621 176.829759 43.211334 176.747338 43.422994 176.664449 43.634603 176.581052 43.846159 176.497134 44.057659 176.4127 44.269105 176.327764 44.480498 176.242285 44.691834 176.156255 44.903112 176.069697 45.114335 175.982589 45.325499 175.894906 45.536605 175.806643 45.74765 175.717834 45.958637 175.628425 46.169563 179.273307 46.849842 179.349067 46.637237 179.424361 46.42459 179.499266 46.21191 179.573725 45.99919 179.647736 45.786431 179.721333 45.573636 179.794548 45.360805 179.867336 45.147938 179.939702 44.935032 180.0 44.75671719951115 180.0 34.027729344730545"}]
                         }]
             }
        ]
        
        events = self.query_eboa.get_events(gauge_names = {"filter": "GAUGE_NAME", "op": "=="},
                                            start_filters = [{"date": "2018-07-21T10:00:00", "op": "=="}],
                                            stop_filters = [{"date": "2018-07-21T10:04:00", "op": "=="}])

        assert len(events) == 1

        footprints = [footprint for footprint in events[0].eventGeometries if footprint.name == "footprint"]
        footprints.sort(key=lambda x: x.parent_position)

        assert len(footprints) == 2

        assert footprints[0].to_wkt()["value"] == "POLYGON ((-179.427364 32.145203, -179.491322 32.358931, -179.555539 32.572629, -179.620015 32.786296, -179.684733 32.999933, -179.74972 33.213539, -179.81498 33.427113, -179.880499 33.640656, -179.946285 33.854168, -180 34.02772934473055, -180 44.75671719951115, -179.988292 44.722094, -179.916675 44.50912, -179.845461 44.296111, -179.774635 44.083066, -179.704137 43.86999, -179.634025 43.656879, -179.564295 43.443734, -179.4949 43.230556, -179.425843 43.017347, -179.357151 42.804105, -179.288819 42.590829, -179.220775 42.377525, -179.153078 42.164188, -179.085726 41.950819, -179.018688 41.737419, -178.951943 41.523991, -178.885529 41.310532, -178.819441 41.097041, -178.753624 40.883523, -178.688108 40.669976, -178.622906 40.456399, -178.558001 40.242793, -178.493346 40.02916, -178.428993 39.815499, -178.364935 39.601808, -178.301133 39.388091, -178.237593 39.174348, -178.174337 38.960576, -178.111362 38.746776, -178.048602 38.532953, -177.986116 38.319103, -177.923898 38.105225, -177.861923 37.891322, -177.800173 37.677395, -177.738682 37.463441, -177.677447 37.249462, -177.616416 37.03546, -177.555622 36.821432, -177.495074 36.60738, -177.434756 36.393303, -177.374631 36.179204, -177.314742 35.965081, -177.255085 35.750933, -177.195623 35.536763, -177.136367 35.32257, -177.077334 35.108354, -177.018521 34.894115, -176.959871 34.679855, -176.901436 34.465572, -176.843214 34.251267, -176.785178 34.03694, -176.727317 33.822593, -176.669661 33.608223, -176.612206 33.393832, -176.554905 33.179421, -176.497792 32.964989, -176.440872 32.750536, -179.427364 32.145203))"

        assert footprints[1].to_wkt()["value"] == "POLYGON ((180 34.02772934473055, 179.987646 34.067647, 179.921292 34.281093, 179.854676 34.494507, 179.787768 34.707887, 179.720563 34.921234, 179.653069 35.134546, 179.585289 35.347825, 179.517202 35.561069, 179.448802 35.774278, 179.38011 35.987452, 179.311106 36.20059, 179.241778 36.413691, 179.172127 36.626756, 179.102171 36.839785, 179.031878 37.052776, 178.961244 37.265729, 178.890285 37.478644, 178.81899 37.691522, 178.747341 37.904359, 178.675333 38.117157, 178.602997 38.329917, 178.530292 38.542636, 178.457215 38.755314, 178.383775 38.96795, 178.309973 39.180547, 178.235784 39.3931, 178.161202 39.605611, 178.086253 39.81808, 178.010908 40.030505, 177.935153 40.242886, 177.858994 40.455222, 177.782446 40.667515, 177.705472 40.879762, 177.628068 41.091962, 177.550253 41.304117, 177.47201 41.516225, 177.393318 41.728285, 177.314174 41.940296, 177.234609 42.152262, 177.154578 42.364177, 177.074073 42.576041, 176.993108 42.787856, 176.91168 42.999621, 176.829759 43.211334, 176.747338 43.422994, 176.664449 43.634603, 176.581052 43.846159, 176.497134 44.057659, 176.4127 44.269105, 176.327764 44.480498, 176.242285 44.691834, 176.156255 44.903112, 176.069697 45.114335, 175.982589 45.325499, 175.894906 45.536605, 175.806643 45.74765, 175.717834 45.958637, 175.628425 46.169563, 179.273307 46.849842, 179.349067 46.637237, 179.424361 46.42459, 179.499266 46.21191, 179.573725 45.99919, 179.647736 45.786431, 179.721333 45.573636, 179.794548 45.360805, 179.867336 45.147938, 179.939702 44.935032, 180 44.75671719951115, 180 34.02772934473055))"

        data = {"operations": [{
            "mode": "insert_and_erase",
            "dim_signature": {"name": "dim_signature",
                              "exec": "exec",
                              "version": "1.0"},
            "source": {"name": "source1.xml",
                       "reception_time": "2018-06-06T13:33:29",
                       "generation_time": "2020-07-05T02:07:03",
                       "validity_start": "2014-07-05T02:07:03",
                       "validity_stop": "2018-07-21T10:01:00"}
        }]
        }

        exit_status = self.engine_eboa.treat_data(data)

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        events = self.query_eboa.get_events(gauge_names = {"filter": "GAUGE_NAME", "op": "=="},
                                            start_filters = [{"date": "2018-07-21T10:01:00", "op": "=="}],
                                            stop_filters = [{"date": "2018-07-21T10:04:00", "op": "=="}])

        assert len(events) == 1

        assert events[0].get_structured_values() == [
            {"type": "text",
             "name": "satellite",
             "value": "S2A"},
            {"type": "object",
             "name": "footprint_details_0",
             "values": [
                 {"type": "geometry",
                  "name": "footprint",
                  "value": "POLYGON ((-180 35.77042462822262, -180 44.75666858978662, -179.980974 44.700363, -179.908663 44.485213, -179.836761 44.270026, -179.765262 44.054803, -179.694105 43.839547, -179.623325 43.624257, -179.552931 43.408932, -179.482912 43.193572, -179.413204 42.978183, -179.343867 42.762759, -179.274895 42.547301, -179.206254 42.331811, -179.137928 42.116291, -179.069952 41.900739, -179.00232 41.685154, -178.934981 41.469539, -178.867958 41.253895, -178.801265 41.038219, -178.734897 40.822512, -178.668786 40.606778, -178.602993 40.391013, -178.537513 40.175219, -178.472319 39.959395, -178.407387 39.743545, -178.342755 39.527665, -178.278419 39.311757, -178.214335 39.095822, -178.150517 38.87986, -178.086982 38.663869, -178.023728 38.447851, -177.960692 38.231809, -177.897926 38.015739, -177.835428 37.799642, -177.77318 37.583519, -177.711151 37.367373, -177.64938 37.1512, -177.587863 36.935, -177.526564 36.718777, -177.465489 36.50253, -177.404658 36.286257, -180 35.77042462822262))"
                  }]},
            {"type": "object",
             "name": "footprint_details_1",
             "values": [
                 {"type": "geometry",
                  "name": "footprint",
                  "value": "POLYGON ((180 35.77042462822262, 179.483044 35.667678, 179.413801 35.883045, 179.344234 36.098375, 179.274353 36.313668, 179.204157 36.528925, 179.133625 36.744144, 179.062751 36.959325, 178.991556 37.174468, 178.920021 37.389573, 178.848131 37.604638, 178.775883 37.819663, 178.703304 38.034649, 178.630357 38.249595, 178.557036 38.464499, 178.48335 38.679362, 178.409304 38.894184, 178.334869 39.108963, 178.260041 39.323699, 178.184839 39.538393, 178.109246 39.753043, 178.033243 39.967649, 177.956825 40.182209, 177.880025 40.396726, 177.802799 40.611197, 177.725143 40.825621, 177.647059 41.039998, 177.568561 41.25433, 177.489613 41.468613, 177.41021 41.682847, 177.330369 41.897033, 177.250076 42.111171, 177.16931 42.325257, 177.088062 42.539292, 177.006364 42.753278, 176.924177 42.967212, 176.841488 43.181092, 176.758299 43.394919, 176.67463 43.608695, 176.590438 43.822415, 176.505716 44.03608, 176.42048 44.249689, 176.33472 44.463244, 176.248407 44.67674, 176.161533 44.890178, 176.074129 45.10356, 175.986156 45.316882, 175.897597 45.530143, 175.808451 45.743343, 175.718743 45.956485, 175.628425 46.169563, 179.273307 46.849842, 179.349838 46.635067, 179.425895 46.420251, 179.50155 46.205398, 179.576754 45.990507, 179.651505 45.775575, 179.725821 45.560606, 179.799758 45.345602, 179.873262 45.130559, 179.946337 44.915479, 180 44.75666858978662, 180 35.77042462822262))"}]
             }]
