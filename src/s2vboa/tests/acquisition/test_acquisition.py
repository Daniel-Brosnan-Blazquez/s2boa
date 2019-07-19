"""
Automated tests for the acquisition view

Written by DEIMOS Space S.L. (femd)

module vboa
"""
import os
import sys
import unittest
import time
import subprocess
import datetime
import s2vboa.tests.acquisition.aux_functions as functions
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains,TouchActions
from selenium.webdriver.common.keys import Keys

# Import engine of the DDBB
import eboa.engine.engine as eboa_engine
import eboa.ingestion.eboa_ingestion as ingestion
import eboa.triggering.eboa_triggering as triggering
from eboa.engine.engine import Engine
from eboa.engine.query import Query
from eboa.datamodel.base import Session, engine, Base
from eboa.engine.errors import UndefinedEventLink, DuplicatedEventLinkRef, WrongPeriod, SourceAlreadyIngested, WrongValue, OddNumberOfCoordinates, EboaResourcesPathNotAvailable, WrongGeometry
from eboa.debugging import debug


class TestAcquisitionView(unittest.TestCase):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('window-size=1920,1080')
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)

    def setUp(self):
        # Create the engine to manage the data
        self.engine_eboa = Engine()
        self.query_eboa = Query()

        # Create session to connect to the database
        self.session = Session()

        # Clear all tables before executing the test
        self.query_eboa.clear_db()

    def tearDown(self):
        # Close connections to the DDBB
        self.engine_eboa.close_session()
        self.query_eboa.close_session()
        self.session.close()

    @classmethod
    def tearDownClass(self):
        self.driver.quit()

    def test_acquisition_no_data(self):

        wait = WebDriverWait(self.driver,5);

        self.driver.get("http://localhost:5000/views/acquisition")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "17600", stop_orbit = "17800", table_details = True, map = True, station_reports = True)

        # Check header generated
        header_no_data = wait.until(EC.visibility_of_element_located((By.ID,"header-no-data")))

        assert header_no_data

        table_details_no_data = wait.until(EC.visibility_of_element_located((By.ID,"acquisition-details-no-acquisitions")))

        assert table_details_no_data

        map_no_data = wait.until(EC.visibility_of_element_located((By.ID,"acquisition-map-no-acquisitions")))

        assert map_no_data

        station_reports_no_data = wait.until(EC.visibility_of_element_located((By.ID,"station-reports-no-reports")))

        assert station_reports_no_data

    def test_acquisition_only_nppf(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]
        
        wait = WebDriverWait(self.driver,5);

        self.driver.get("http://localhost:5000/views/acquisition")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "17600", stop_orbit = "17800", table_details = True, map = True, station_reports = True)

        # Check header generated
        header_no_data = wait.until(EC.visibility_of_element_located((By.ID,"header-no-data")))

        assert header_no_data

        table_details_no_data = wait.until(EC.visibility_of_element_located((By.ID,"acquisition-details-no-acquisitions")))

        assert table_details_no_data

        map_no_data = wait.until(EC.visibility_of_element_located((By.ID,"acquisition-map-no-acquisitions")))

        assert map_no_data

        station_reports_no_data = wait.until(EC.visibility_of_element_located((By.ID,"station-reports-no-reports")))

        assert station_reports_no_data

    def test_acquisition_only_nppf_and_orbpre(self):
        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        wait = WebDriverWait(self.driver,5);

        self.driver.get("http://localhost:5000/views/acquisition")

        functions.query(self.driver, wait, "S2A", start = "2018-07-20T00:00:14", stop = "2018-07-21T23:55:14", start_orbit = "16066", stop_orbit = "16072", table_details = True, map = True, station_reports = True)

        # Header

        header_table = self.driver.find_element_by_id("header-table")

        orbit_start = header_table.find_element_by_xpath("tbody/tr[th[text() = 'Orbit information']]/td[1]")

        assert orbit_start.text == "16077"

        orbit_stop = header_table.find_element_by_xpath("tbody/tr[th[text() = 'Orbit information']]/td[2]")

        assert orbit_stop.text == "16079"

        time_start = header_table.find_element_by_xpath("tbody/tr[th[text() = 'Time information']]/td[1]")

        assert time_start.text == "2018-07-20T00:00:14"

        time_stop = header_table.find_element_by_xpath("tbody/tr[th[text() = 'Time information']]/td[2]")

        assert time_stop.text == "2018-07-21T23:55:14"

        #Acquisitions table

        acquisition_details_table = self.driver.find_element_by_id("acquisition-details-table")

        satellite = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        orbit = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert orbit.text == "16078"

        station = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == ""

        playback_type = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert playback_type.text == "NOMINAL"

        parameters = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert parameters.text == "MEM_FREE=1\nSCN_DUP=0\nSCN_RWD=1"

        playback_status = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert playback_status.text == "MISSING"

        start = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert start.text == "2018-07-21T10:35:32.524661"

        stop = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert stop.text == "2018-07-21T10:37:08.530863"

        duration_s = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert duration_s.text == "96.006"

        duration_m = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert duration_m.text == "1.6"

        station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert station_schedule.text == "MISSING"

        dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert station_schedule.text == "MISSING"

        delta_start_acq = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[13]")

        assert delta_start_acq.text == "N/A"

        delta_stop_acq = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[14]")

        assert delta_stop_acq.text == "N/A"

        delta_start_station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[15]")

        assert delta_start_station_schedule.text == "N/A"

        delta_stop_station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[16]")

        assert delta_stop_station_schedule.text == "N/A"

        delta_start_dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[17]")

        assert delta_start_dfep_schedule.text == "N/A"

        delta_stop_dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[18]")

        assert delta_stop_dfep_schedule.text == "N/A"

        plan_file = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[19]")

        assert plan_file.text == "S2A_NPPF.EOF"

        uuid = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[21]")

        assert re.match("........-....-....-....-............", uuid.text)

        original_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"like"})

        original_events.sort(key=lambda x:x.start)

        corrected_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_CORRECTION", "op":"like"})

        corrected_events.sort(key=lambda x:x.start)

        # Timeline
        acquisition_timeline_missing = [
            {"id": str(corrected_events[0].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:35:32.524661",
             "stop": "2018-07-21T10:37:08.530863",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td>" +
                          "<tr><td>Satellite</td><td>S2A</td>" +
                          "<tr><td>Orbit</td><td>16078</td>" +
                          "<tr><td>Station</td><td></td>" +
                          "<tr><td>Status</td><td><span class='bold-red'>MISSING</span></td>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:32.524661</td>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:08.530863</td>" +
                          "<tr><td>Duration(m)</td><td>1.600</td>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td>" +
                          "<tr><td>Playback mean</td><td>XBAND</td>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td>' +
                          "</tr></table>",
            "className": "background-red"
             },
            {"id": str(corrected_events[1].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:37:19.534390",
             "stop": "2018-07-21T10:37:19.534390",
             "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td>" +
                          "<tr><td>Satellite</td><td>S2A</td>" +
                          "<tr><td>Orbit</td><td>16078</td>" +
                          "<tr><td>Station</td><td></td>" +
                          "<tr><td>Status</td><td><span class='bold-red'>MISSING</span></td>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:19.534390</td>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:19.534390</td>" +
                          "<tr><td>Duration(m)</td><td>0.000</td>" +
                          "<tr><td>Playback type</td><td>SAD</td>" +
                          "<tr><td>Playback mean</td><td>XBAND</td>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td>' +
                          "</tr></table>",
              "className": "background-red"
            }
        ]

        assert acquisition_timeline_missing == self.driver.execute_script('return missing_playbacks_timeline;')

        # Map

        acquisition_geometries_missing = [
            {"id": str(corrected_events[0].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td>" +
                          "<tr><td>Satellite</td><td>S2A</td>" +
                          "<tr><td>Orbit</td><td>16078</td>" +
                          "<tr><td>Station</td><td></td>" +
                          "<tr><td>Status</td><td><span class='bold-red'>MISSING</span></td>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:32.524661</td>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:08.530863</td>" +
                          "<tr><td>Duration(m)</td><td>1.600</td>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td>" +
                          "<tr><td>Playback mean</td><td>XBAND</td>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td>' +
                          "</tr></table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((3.087722 19.617211, 3.033528 19.398861, 2.979462 19.180495, 2.925521 18.962114, 2.8717 18.743717, 2.817995 18.525305, 2.76441 18.306878, 2.710944 18.088436, 2.65759 17.86998, 2.604348 17.651509, 2.55122 17.433025, 2.498205 17.214526, 2.445294 16.996013, 2.392491 16.777487, 2.339796 16.558948, 2.287207 16.340395, 2.234717 16.12183, 2.18233 15.903252, 2.130046 15.684661, 2.077859 15.466058, 2.025768 15.247442, 1.973776 15.028815, 1.921879 14.810176, 1.870074 14.591525, 1.818361 14.372862, 1.766741 14.154189, 1.715211 13.935504, -0.889933 14.505031, -0.840898 14.723922, -0.791809 14.942805, -0.742666 15.161681, -0.693477 15.38055, -0.644248 15.599413, -0.594961 15.818267, -0.545614 16.037113, -0.496225 16.255952, -0.446784 16.474783, -0.39728 16.693606, -0.347711 16.91242, -0.298103 17.131227, -0.248431 17.350024, -0.198691 17.568813, -0.148886 17.787592, -0.099036 18.006363, -0.049114 18.225125, 0.000882 18.443877, 0.050939 18.662619, 0.101054 18.881352, 0.151247 19.100075, 0.201518 19.318788, 0.251847 19.537491, 0.302248 19.756183, 0.352731 19.974865, 0.403298 20.193536, 3.087722 19.617211))"
              }],
             "style": {
                 "stroke_color": "red",
                 "fill_color": "rgba(255,0,0,0.3)",
             }
             },
             {"id": str(corrected_events[1].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td>" +
                          "<tr><td>Satellite</td><td>S2A</td>" +
                          "<tr><td>Orbit</td><td>16078</td>" +
                          "<tr><td>Station</td><td></td>" +
                          "<tr><td>Status</td><td><span class='bold-red'>MISSING</span></td>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:19.534390</td>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:19.534390</td>" +
                          "<tr><td>Duration(m)</td><td>0.000</td>" +
                          "<tr><td>Playback type</td><td>SAD</td>" +
                          "<tr><td>Playback mean</td><td>XBAND</td>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td>' +
                          "</tr></table>",
              "geometries":[{
                     "name": "footprint",
                  "value": "POLYGON ((1.562169 13.283776, -1.035823 13.852714, -1.035823 13.852714, 1.562169 13.283776))"
              }],
              "style": {
                  "stroke_color": "red",
                  "fill_color": "rgba(255,0,0,0.3)",
              }
            }
        ]

        assert acquisition_geometries_missing == self.driver.execute_script('return acquisition_geometries_missing;')

        station_reports_no_data = wait.until(EC.visibility_of_element_located((By.ID,"station-reports-no-reports")))

        assert station_reports_no_data

    def test_acquisition_only_nppf_orbpre_and_rep_pass(self):
        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_REP_PASS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        wait = WebDriverWait(self.driver,5);

        self.driver.get("http://localhost:5000/views/acquisition")

        functions.query(self.driver, wait, "S2A", start = "2018-07-20T00:00:14", stop = "2018-07-21T23:55:14", start_orbit = "16066", stop_orbit = "16072", table_details = True, map = True, station_reports = True)

        # Header

        header_table = self.driver.find_element_by_id("header-table")

        orbit_start = header_table.find_element_by_xpath("tbody/tr[th[text() = 'Orbit information']]/td[1]")

        assert orbit_start.text == "16077"

        orbit_stop = header_table.find_element_by_xpath("tbody/tr[th[text() = 'Orbit information']]/td[2]")

        assert orbit_stop.text == "16079"

        time_start = header_table.find_element_by_xpath("tbody/tr[th[text() = 'Time information']]/td[1]")

        assert time_start.text == "2018-07-20T00:00:14"

        time_stop = header_table.find_element_by_xpath("tbody/tr[th[text() = 'Time information']]/td[2]")

        assert time_stop.text == "2018-07-21T23:55:14"

        #Acquisitions table

        acquisition_details_table = self.driver.find_element_by_id("acquisition-details-table")

        satellite = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        orbit = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert orbit.text == "16078"

        station = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == ""

        playback_type = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert playback_type.text == "NOMINAL"

        parameters = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert parameters.text == "MEM_FREE=1\nSCN_DUP=0\nSCN_RWD=1"

        playback_status = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert playback_status.text == "RECEIVED"

        start = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert start.text == "2018-07-21T10:35:32.524661"

        stop = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert stop.text == "2018-07-21T10:37:08.530863"

        duration_s = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert duration_s.text == "96.006"

        duration_m = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert duration_m.text == "1.6"

        station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert station_schedule.text == "MISSING"

        dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert station_schedule.text == "MISSING"

        delta_start_acq = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[13]")

        assert delta_start_acq.text == "-1.204"

        delta_stop_acq = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[14]")

        assert delta_stop_acq.text == "-6.189"

        delta_start_station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[15]")

        assert delta_start_station_schedule.text == "N/A"

        delta_stop_station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[16]")

        assert delta_stop_station_schedule.text == "N/A"

        delta_start_dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[17]")

        assert delta_start_dfep_schedule.text == "N/A"

        delta_stop_dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[18]")

        assert delta_stop_dfep_schedule.text == "N/A"

        plan_file = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[19]")

        assert plan_file.text == "S2A_NPPF.EOF"

        uuid = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[21]")

        assert re.match("........-....-....-....-............", uuid.text)


        original_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"like"})

        original_events.sort(key=lambda x:x.start)

        playback_completeness_channel_1 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_1", "op":"like"})

        playback_completeness_channel_1.sort(key=lambda x:x.start)

        playback_completeness_channel_2 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2", "op":"like"})

        playback_completeness_channel_2.sort(key=lambda x:x.start)

        # Timeline
        acquisition_timeline_received = [
            {"id": str(playback_completeness_channel_1[0].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:35:33.728601",
             "stop": "2018-07-21T10:37:14.719834",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td>" +
                          "<tr><td>Satellite</td><td>S2A</td>" +
                          "<tr><td>Orbit</td><td>16078</td>" +
                          "<tr><td>Station</td><td></td>" +
                          "<tr><td>Status</td><td><span class='bold-green'>RECEIVED</span></td>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.728601</td>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.719834</td>" +
                          "<tr><td>Duration(m)</td><td>1.683</td>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td>" +
                          "<tr><td>Playback mean</td><td>XBAND</td>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td>' +
                          "</tr></table>",
            "className": "background-green"
             },
            {"id": str(playback_completeness_channel_2[0].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:35:33.760977",
             "stop": "2018-07-21T10:37:14.753003",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td>" +
                          "<tr><td>Satellite</td><td>S2A</td>" +
                          "<tr><td>Orbit</td><td>16078</td>" +
                          "<tr><td>Station</td><td></td>" +
                          "<tr><td>Status</td><td><span class='bold-green'>RECEIVED</span></td>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.760977</td>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.753003</td>" +
                          "<tr><td>Duration(m)</td><td>1.683</td>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td>" +
                          "<tr><td>Playback mean</td><td>XBAND</td>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td>' +
                          "</tr></table>",
            "className": "background-green"
             },
            {"id": str(playback_completeness_channel_2[1].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:37:20.858708",
             "stop": "2018-07-21T10:37:26.355940",
             "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td>" +
                          "<tr><td>Satellite</td><td>S2A</td>" +
                          "<tr><td>Orbit</td><td>16078</td>" +
                          "<tr><td>Station</td><td></td>" +
                          "<tr><td>Status</td><td><span class='bold-green'>RECEIVED</span></td>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:20.858708</td>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:26.355940</td>" +
                          "<tr><td>Duration(m)</td><td>0.092</td>" +
                          "<tr><td>Playback type</td><td>SAD</td>" +
                          "<tr><td>Playback mean</td><td>XBAND</td>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td>' +
                          "</tr></table>",
              "className": "background-green"
            }
        ]

        assert acquisition_timeline_received == self.driver.execute_script('return received_playbacks_timeline;')

        # Map

        acquisition_geometries_received = [
            {"id": str(playback_completeness_channel_1[0].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td>" +
                          "<tr><td>Satellite</td><td>S2A</td>" +
                          "<tr><td>Orbit</td><td>16078</td>" +
                          "<tr><td>Station</td><td></td>" +
                          "<tr><td>Status</td><td><span class='bold-green'>RECEIVED</span></td>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.728601</td>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.719834</td>" +
                          "<tr><td>Duration(m)</td><td>1.683</td>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td>" +
                          "<tr><td>Playback mean</td><td>XBAND</td>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td>' +
                          "</tr></table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((3.070036 19.546021, 3.015189 19.324835, 2.960462 19.103632, 2.905864 18.882414, 2.851391 18.66118, 2.79704 18.439931, 2.742805 18.218667, 2.688691 17.997387, 2.634696 17.776092, 2.580816 17.554783, 2.527047 17.33346, 2.473393 17.112122, 2.419851 16.89077, 2.366418 16.669405, 2.31309 16.448025, 2.259871 16.226633, 2.206759 16.005227, 2.153748 15.783808, 2.100839 15.562377, 2.048032 15.340932, 1.995326 15.119476, 1.942715 14.898007, 1.890201 14.676526, 1.837783 14.455034, 1.785461 14.233529, 1.733228 14.012014, 1.681087 13.790487, 1.629037 13.568949, -0.972041 14.138141, -0.92244 14.35988, -0.872787 14.581612, -0.823084 14.803337, -0.773348 15.025056, -0.723556 15.246768, -0.673708 15.468471, -0.623807 15.690167, -0.573867 15.911855, -0.523867 16.133536, -0.473804 16.355208, -0.423688 16.576872, -0.373525 16.798528, -0.323296 17.020175, -0.273 17.241813, -0.222649 17.463442, -0.172242 17.685063, -0.121765 17.906674, -0.071215 18.128275, -0.02061 18.349867, 0.03006 18.57145, 0.080806 18.793023, 0.13163 19.014585, 0.182511 19.236137, 0.233464 19.457679, 0.2845 19.67921, 0.335619 19.90073, 0.386797 20.122241, 3.070036 19.546021))"
              }],
             "style": {
                 "stroke_color": "green",
                 "fill_color": "rgba(0,255,0,0.3)",
             }
             },
            {"id": str(playback_completeness_channel_2[0].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td>" +
                          "<tr><td>Satellite</td><td>S2A</td>" +
                          "<tr><td>Orbit</td><td>16078</td>" +
                          "<tr><td>Station</td><td></td>" +
                          "<tr><td>Status</td><td><span class='bold-green'>RECEIVED</span></td>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.760977</td>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.753003</td>" +
                          "<tr><td>Duration(m)</td><td>1.683</td>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td>" +
                          "<tr><td>Playback mean</td><td>XBAND</td>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td>' +
                          "</tr></table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((3.069561 19.544106, 3.014714 19.322918, 2.959988 19.101714, 2.90539 18.880494, 2.850918 18.659258, 2.796568 18.438007, 2.742333 18.216741, 2.68822 17.995459, 2.634226 17.774163, 2.580346 17.552852, 2.526578 17.331527, 2.472924 17.110187, 2.419383 16.888833, 2.36595 16.667466, 2.312623 16.446085, 2.259405 16.22469, 2.206293 16.003283, 2.153283 15.781862, 2.100374 15.560429, 2.047568 15.338983, 1.994862 15.117524, 1.942252 14.896053, 1.889738 14.674571, 1.837321 14.453076, 1.784999 14.23157, 1.732766 14.010053, 1.680625 13.788524, 1.628576 13.566984, -0.972481 14.136174, -0.92288 14.357915, -0.8732259999999999 14.579649, -0.823524 14.801376, -0.773787 15.023097, -0.723996 15.24481, -0.6741470000000001 15.466515, -0.624248 15.688213, -0.574308 15.909904, -0.524307 16.131586, -0.474244 16.35326, -0.424129 16.574925, -0.373965 16.796583, -0.323736 17.018232, -0.27344 17.239872, -0.22309 17.461503, -0.172684 17.683126, -0.122206 17.904738, -0.071657 18.126341, -0.021051 18.347936, 0.029618 18.56952, 0.080364 18.791094, 0.131188 19.012658, 0.182068 19.234212, 0.233022 19.455756, 0.284057 19.677289, 0.335176 19.898811, 0.386353 20.120323, 3.069561 19.544106))"
              }],
             "style": {
                 "stroke_color": "green",
                 "fill_color": "rgba(0,255,0,0.3)",
             }
             },
             {"id": str(playback_completeness_channel_2[1].event_uuid),
             "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td>" +
                          "<tr><td>Satellite</td><td>S2A</td>" +
                          "<tr><td>Orbit</td><td>16078</td>" +
                          "<tr><td>Station</td><td></td>" +
                          "<tr><td>Status</td><td><span class='bold-green'>RECEIVED</span></td>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:20.858708</td>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:26.355940</td>" +
                          "<tr><td>Duration(m)</td><td>0.092</td>" +
                          "<tr><td>Playback type</td><td>SAD</td>" +
                          "<tr><td>Playback mean</td><td>XBAND</td>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td>' +
                          "</tr></table>",
              "geometries":[{
                     "name": "footprint",
                  "value": "POLYGON ((1.543801 13.205331, 1.467672 12.879696, -1.126077 13.448288, -1.053359 13.774202, 1.543801 13.205331))"
              }],
              "style": {
                  "stroke_color": "green",
                  "fill_color": "rgba(0,255,0,0.3)",
              }
            }
        ]

        assert acquisition_geometries_received == self.driver.execute_script('return acquisition_geometries_received;')

        station_reports_no_data = wait.until(EC.visibility_of_element_located((By.ID,"station-reports-no-reports")))

        assert station_reports_no_data

    def test_acquisition_only_nppf_orbpre_and_station_report(self):

        filename = "S2A_NPPF_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_STNACQ.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_station_acquisition_report.ingestion_station_acquisition_report", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]


    def test_acquisition_mixing_received_and_missing(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_MPL_SPMPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_REP_PASS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]
        
        filename = "S2A_NPPF_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_STNACQ.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_station_acquisition_report.ingestion_station_acquisition_report", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]
