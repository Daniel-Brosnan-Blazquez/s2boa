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

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

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

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

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

        satellite = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[1]")

        assert satellite.text == "S2A"

        orbit = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[2]")

        assert orbit.text == "16078"

        station = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[3]")

        assert station.text == ""

        playback_type = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[4]")

        assert playback_type.text == "NOMINAL"

        playback_status = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[5]")

        assert playback_status.text == "MISSING"

        playback_isp_completeness = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[6]")

        assert playback_isp_completeness.text == "N/A"

        playback_missing_packets = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[7]")

        assert playback_missing_packets.text == "N/A"

        link_session = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[8]")

        assert link_session.text == "N/A"

        start = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[9]")

        assert start.text == "2018-07-21T10:35:32.524661"

        stop = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[10]")

        assert stop.text == "2018-07-21T10:37:08.530863"

        duration_s = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[11]")

        assert duration_s.text == "96.006"

        duration_m = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[12]")

        assert duration_m.text == "1.6"

        parameters = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[13]")

        assert parameters.text == "MEM_FREE=1\nSCN_DUP=0\nSCN_RWD=1"

        station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[14]")

        assert station_schedule.text == "MISSING"

        dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[15]")

        assert station_schedule.text == "MISSING"

        delta_start_acq = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[16]")

        assert delta_start_acq.text == "N/A"

        delta_stop_acq = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[17]")

        assert delta_stop_acq.text == "N/A"

        delta_start_station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[18]")

        assert delta_start_station_schedule.text == "N/A"

        delta_stop_station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[19]")

        assert delta_stop_station_schedule.text == "N/A"

        delta_start_dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[20]")

        assert delta_start_dfep_schedule.text == "N/A"

        delta_stop_dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[21]")

        assert delta_stop_dfep_schedule.text == "N/A"

        plan_file = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[22]")

        assert plan_file.text == "S2A_NPPF.EOF"

        uuid = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[24]")

        assert re.match("........-....-....-....-............", uuid.text)

        original_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"=="})

        original_events.sort(key=lambda x:x.start)

        corrected_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_CORRECTION", "op":"=="})

        corrected_events.sort(key=lambda x:x.start)

        playback_completeness_channel_1 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_1", "op":"=="})

        playback_completeness_channel_1.sort(key=lambda x:x.start)

        playback_completeness_channel_2 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2", "op":"=="})

        playback_completeness_channel_2.sort(key=lambda x:x.start)
        
        # Timeline
        acquisition_timeline_missing = [
            {"id": str(playback_completeness_channel_1[0].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:35:41.524661",
             "stop": "2018-07-21T10:36:59.530863",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:41.524661</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:36:59.530863</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.300</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-red"
             },
            {"id": str(playback_completeness_channel_2[0].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:35:41.524661",
             "stop": "2018-07-21T10:36:59.530863",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:41.524661</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:36:59.530863</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.300</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-red"
             },
            {"id": str(playback_completeness_channel_2[1].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:37:21.534390",
             "stop": "2018-07-21T10:37:21.534390",
             "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:21.534390</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:21.534390</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                          "<tr><td>Playback type</td><td>SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "className": "fill-border-red"
            }
        ]

        returned_missing_playbacks_timeline = self.driver.execute_script('return missing_playbacks_timeline;')
        returned_missing_playbacks_timeline.sort(key=lambda x:x["start"])
        assert acquisition_timeline_missing == returned_missing_playbacks_timeline

        # Map

        acquisition_geometries_missing = [
            {"id": str(playback_completeness_channel_1[0].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:41.524661</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:36:59.530863</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.300</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((2.955857 19.08499, 2.901645 18.865298, 2.847556 18.645591, 2.79359 18.425869, 2.739736 18.206132, 2.686002 17.98638, 2.632386 17.766613, 2.578883 17.546832, 2.525488 17.327037, 2.472207 17.107227, 2.419038 16.887404, 2.365975 16.667567, 2.313016 16.447717, 2.260165 16.227854, 2.207419 16.007977, 2.154772 15.788088, 2.102226 15.568186, 2.049781 15.348272, 1.997435 15.128345, 1.945183 14.908407, 1.893027 14.688456, 1.840966 14.468494, -0.770322 15.03853, -0.720873 15.258709, -0.671367 15.478881, -0.621807 15.699045, -0.572211 15.919203, -0.522554 16.139352, -0.472837 16.359492, -0.423065 16.579625, -0.373248 16.79975, -0.323366 17.019866, -0.273417 17.239973, -0.223415 17.460072, -0.173358 17.680162, -0.123231 17.900243, -0.073031 18.120314, -0.02278 18.340376, 0.027537 18.560429, 0.07793 18.780471, 0.1284 19.000503, 0.178921 19.220526, 0.229519 19.440539, 0.280198 19.660541, 2.955857 19.08499))"
              }],
             "style": {
                 "stroke_color": "red",
                 "fill_color": "rgba(255,0,0,0.3)",
             }
             },
            {"id": str(playback_completeness_channel_2[0].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:41.524661</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:36:59.530863</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.300</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((2.955857 19.08499, 2.901645 18.865298, 2.847556 18.645591, 2.79359 18.425869, 2.739736 18.206132, 2.686002 17.98638, 2.632386 17.766613, 2.578883 17.546832, 2.525488 17.327037, 2.472207 17.107227, 2.419038 16.887404, 2.365975 16.667567, 2.313016 16.447717, 2.260165 16.227854, 2.207419 16.007977, 2.154772 15.788088, 2.102226 15.568186, 2.049781 15.348272, 1.997435 15.128345, 1.945183 14.908407, 1.893027 14.688456, 1.840966 14.468494, -0.770322 15.03853, -0.720873 15.258709, -0.671367 15.478881, -0.621807 15.699045, -0.572211 15.919203, -0.522554 16.139352, -0.472837 16.359492, -0.423065 16.579625, -0.373248 16.79975, -0.323366 17.019866, -0.273417 17.239973, -0.223415 17.460072, -0.173358 17.680162, -0.123231 17.900243, -0.073031 18.120314, -0.02278 18.340376, 0.027537 18.560429, 0.07793 18.780471, 0.1284 19.000503, 0.178921 19.220526, 0.229519 19.440539, 0.280198 19.660541, 2.955857 19.08499))"
              }],
             "style": {
                 "stroke_color": "red",
                 "fill_color": "rgba(255,0,0,0.3)",
             }
             },
             {"id": str(playback_completeness_channel_2[1].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:21.534390</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:21.534390</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                          "<tr><td>Playback type</td><td>SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                  "value": "POLYGON ((1.534434 13.165308, -1.062301 13.734143, -1.062301 13.734143, 1.534434 13.165308))"
              }],
              "style": {
                  "stroke_color": "red",
                  "fill_color": "rgba(255,0,0,0.3)",
              }
            }
        ]

        returned_acquisition_geometries_missing = self.driver.execute_script('return acquisition_geometries_missing;')
        returned_acquisition_geometries_missing.sort(key=lambda x:x["id"])
        assert acquisition_geometries_missing == returned_acquisition_geometries_missing

        station_reports_no_data = wait.until(EC.visibility_of_element_located((By.ID,"station-reports-no-reports")))

        assert station_reports_no_data

    def test_acquisition_only_nppf_orbpre_and_rep_pass(self):
        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_REP_PASS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

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

        satellite = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[1]")

        assert satellite.text == "S2A"

        orbit = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[2]")

        assert orbit.text == "16078"

        station = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[3]")

        assert station.text == ""

        playback_type = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[4]")

        assert playback_type.text == "NOMINAL"

        playback_status = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[5]")

        assert playback_status.text == "RECEIVED"

        playback_isp_completeness = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[6]")

        assert playback_isp_completeness.text == "OK"

        playback_missing_packets = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[7]")

        assert playback_missing_packets.text == "0"

        link_session = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[8]")

        assert link_session.text == "REP_PASS_2_2018-07-21T10:35:27"

        start = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[9]")

        assert start.text == "2018-07-21T10:35:32.524661"

        stop = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[10]")

        assert stop.text == "2018-07-21T10:37:08.530863"

        duration_s = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[11]")

        assert duration_s.text == "96.006"

        duration_m = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[12]")

        assert duration_m.text == "1.6"

        parameters = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[13]")

        assert parameters.text == "MEM_FREE=1\nSCN_DUP=0\nSCN_RWD=1"

        station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[14]")

        assert station_schedule.text == "MISSING"

        dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[15]")

        assert station_schedule.text == "MISSING"

        delta_start_acq = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[16]")

        assert delta_start_acq.text == "-1.204"

        delta_stop_acq = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[17]")

        assert delta_stop_acq.text == "-6.189"

        delta_start_station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[18]")

        assert delta_start_station_schedule.text == "N/A"

        delta_stop_station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[19]")

        assert delta_stop_station_schedule.text == "N/A"

        delta_start_dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[20]")

        assert delta_start_dfep_schedule.text == "N/A"

        delta_stop_dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[21]")

        assert delta_stop_dfep_schedule.text == "N/A"

        plan_file = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[22]")

        assert plan_file.text == "S2A_NPPF.EOF"

        uuid = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[24]")

        assert re.match("........-....-....-....-............", uuid.text)


        original_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"=="})

        original_events.sort(key=lambda x:x.start)

        corrected_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_CORRECTION", "op":"=="})

        corrected_events.sort(key=lambda x:x.start)

        playback_completeness_channel_1 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_1", "op":"=="})

        playback_completeness_channel_1.sort(key=lambda x:x.start)

        playback_completeness_channel_2 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2", "op":"=="})

        playback_completeness_channel_2.sort(key=lambda x:x.start)

        # Timeline
        acquisition_timeline_received = [
            {"id": str(playback_completeness_channel_1[0].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:35:33.728601",
             "stop": "2018-07-21T10:37:14.719834",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.728601</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.719834</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-green"
             },
            {"id": str(playback_completeness_channel_2[0].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:35:33.760977",
             "stop": "2018-07-21T10:37:14.753003",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.760977</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.753003</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-green"
             },
            {"id": str(playback_completeness_channel_2[1].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:37:20.858708",
             "stop": "2018-07-21T10:37:26.355940",
             "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:20.858708</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:26.355940</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.092</td></tr>" +
                          "<tr><td>Playback type</td><td>SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "className": "fill-border-green"
            }
        ]

        returned_received_playbacks_timeline = self.driver.execute_script('return received_playbacks_timeline;')
        returned_received_playbacks_timeline.sort(key=lambda x:x["start"])
        assert acquisition_timeline_received == returned_received_playbacks_timeline

        # Map

        acquisition_geometries_received = [
            {"id": str(playback_completeness_channel_1[0].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.728601</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.719834</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
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
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.760977</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.753003</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
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
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:20.858708</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:26.355940</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.092</td></tr>" +
                          "<tr><td>Playback type</td><td>SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
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

        returned_acquisition_geometries_received = self.driver.execute_script('return acquisition_geometries_received;')
        returned_acquisition_geometries_received.sort(key=lambda x:x["id"])
        assert acquisition_geometries_received == returned_acquisition_geometries_received

        station_reports_no_data = wait.until(EC.visibility_of_element_located((By.ID,"station-reports-no-reports")))

        assert station_reports_no_data

    def test_acquisition_partial(self):
        filename = "S2A_NPPF_PARTIAL.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_REP_PASS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        wait = WebDriverWait(self.driver,5);

        self.driver.get("http://localhost:5000/views/acquisition")

        functions.query(self.driver, wait, "S2A", start = "2018-07-20T00:00:14", stop = "2018-07-21T23:55:14", start_orbit = "16066", stop_orbit = "16072", table_details = True, map = True, station_reports = True)

        #Acquisitions table

        acquisition_details_table = self.driver.find_element_by_id("acquisition-details-table")

        satellite = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[1]")

        assert satellite.text == "S2A"

        orbit = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[2]")

        assert orbit.text == "16078"

        station = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[3]")

        assert station.text == ""

        playback_type = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[4]")

        assert playback_type.text == "NOMINAL"

        playback_status = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[5]")

        assert playback_status.text == "PARTIAL"

        playback_isp_completeness = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[6]")

        assert playback_isp_completeness.text == "OK"

        playback_missing_packets = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[7]")

        assert playback_missing_packets.text == "0"

        link_session = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[8]")

        assert link_session.text == "REP_PASS_2_2018-07-21T10:35:27"

        start = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[9]")

        assert start.text == "2018-07-21T10:35:15.907236"

        stop = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[10]")

        assert stop.text == "2018-07-21T10:37:08.530863"

        duration_s = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[11]")

        assert duration_s.text == "112.624"

        duration_m = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[12]")

        assert duration_m.text == "1.877"

        parameters = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[13]")

        assert parameters.text == "MEM_FREE=1\nSCN_DUP=0\nSCN_RWD=1"

        station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[14]")

        assert station_schedule.text == "MISSING"

        dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[15]")

        assert station_schedule.text == "MISSING"

        delta_start_acq = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[16]")

        assert delta_start_acq.text == "-17.821"

        delta_stop_acq = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[17]")

        assert delta_stop_acq.text == "-6.189"

        delta_start_station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[18]")

        assert delta_start_station_schedule.text == "N/A"

        delta_stop_station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[19]")

        assert delta_stop_station_schedule.text == "N/A"

        delta_start_dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[20]")

        assert delta_start_dfep_schedule.text == "N/A"

        delta_stop_dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[21]")

        assert delta_stop_dfep_schedule.text == "N/A"

        plan_file = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[22]")

        assert plan_file.text == "S2A_NPPF_PARTIAL.EOF"

        uuid = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[24]")

        assert re.match("........-....-....-....-............", uuid.text)


        original_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"=="})

        original_events.sort(key=lambda x:x.start)

        corrected_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_CORRECTION", "op":"=="})

        corrected_events.sort(key=lambda x:x.start)

        playback_completeness_channel_1 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_1", "op":"=="})

        playback_completeness_channel_1.sort(key=lambda x:x.start)

        playback_completeness_channel_2 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2", "op":"=="})

        playback_completeness_channel_2.sort(key=lambda x:x.start)

        # Received Timeline
        acquisition_timeline_received = [
            {"id": str(playback_completeness_channel_1[1].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:35:33.728601",
             "stop": "2018-07-21T10:37:14.719834",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.728601</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.719834</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_PARTIAL.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-green"
             },
            {"id": str(playback_completeness_channel_2[1].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:35:33.760977",
             "stop": "2018-07-21T10:37:14.753003",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.760977</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.753003</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_PARTIAL.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-green"
             },
            {"id": str(playback_completeness_channel_2[2].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:37:20.858708",
             "stop": "2018-07-21T10:37:26.355940",
             "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:20.858708</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:26.355940</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.092</td></tr>" +
                          "<tr><td>Playback type</td><td>SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_PARTIAL.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "className": "fill-border-green"
            }
        ]

        returned_acquisition_timeline_received = self.driver.execute_script('return received_playbacks_timeline;')
        returned_acquisition_timeline_received.sort(key=lambda x:x["start"])
        assert acquisition_timeline_received == returned_acquisition_timeline_received

        # Missing Timeline
        acquisition_timeline_missing = [
            {"id": str(playback_completeness_channel_1[0].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:35:24.907236",
             "stop": "2018-07-21T10:35:33.728601",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:24.907236</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:35:33.728601</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.147</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_PARTIAL.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-red"
             },
            {"id": str(playback_completeness_channel_2[0].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:35:24.907236",
             "stop": "2018-07-21T10:35:33.760977",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:24.907236</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:35:33.760977</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.148</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_PARTIAL.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-red"
             }
        ]

        returned_missing_playbacks_timeline = self.driver.execute_script('return missing_playbacks_timeline;')
        returned_missing_playbacks_timeline.sort(key=lambda x:x["start"])
        assert acquisition_timeline_missing == returned_missing_playbacks_timeline

        # Map

        acquisition_geometries_received = [
            {"id": str(playback_completeness_channel_1[1].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.728601</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.719834</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_PARTIAL.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((3.070036 19.546021, 3.015189 19.324835, 2.960462 19.103632, 2.905864 18.882414, 2.851391 18.66118, 2.79704 18.439931, 2.742805 18.218667, 2.688691 17.997387, 2.634696 17.776092, 2.580816 17.554783, 2.527047 17.33346, 2.473393 17.112122, 2.419851 16.89077, 2.366418 16.669405, 2.31309 16.448025, 2.259871 16.226633, 2.206759 16.005227, 2.153748 15.783808, 2.100839 15.562377, 2.048032 15.340932, 1.995326 15.119476, 1.942715 14.898007, 1.890201 14.676526, 1.837783 14.455034, 1.785461 14.233529, 1.733228 14.012014, 1.681087 13.790487, 1.629037 13.568949, -0.972041 14.138141, -0.92244 14.35988, -0.872787 14.581612, -0.823084 14.803337, -0.773348 15.025056, -0.723556 15.246768, -0.673708 15.468471, -0.623807 15.690167, -0.573867 15.911855, -0.523867 16.133536, -0.473804 16.355208, -0.423688 16.576872, -0.373525 16.798528, -0.323296 17.020175, -0.273 17.241813, -0.222649 17.463442, -0.172242 17.685063, -0.121765 17.906674, -0.071215 18.128275, -0.02061 18.349867, 0.03006 18.57145, 0.080806 18.793023, 0.13163 19.014585, 0.182511 19.236137, 0.233464 19.457679, 0.2845 19.67921, 0.335619 19.90073, 0.386797 20.122241, 3.070036 19.546021))"
              }],
             "style": {
                 "stroke_color": "green",
                 "fill_color": "rgba(0,255,0,0.3)",
             }
             },
            {"id": str(playback_completeness_channel_2[1].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.760977</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.753003</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_PARTIAL.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((3.069561 19.544106, 3.014714 19.322918, 2.959988 19.101714, 2.90539 18.880494, 2.850918 18.659258, 2.796568 18.438007, 2.742333 18.216741, 2.68822 17.995459, 2.634226 17.774163, 2.580346 17.552852, 2.526578 17.331527, 2.472924 17.110187, 2.419383 16.888833, 2.36595 16.667466, 2.312623 16.446085, 2.259405 16.22469, 2.206293 16.003283, 2.153283 15.781862, 2.100374 15.560429, 2.047568 15.338983, 1.994862 15.117524, 1.942252 14.896053, 1.889738 14.674571, 1.837321 14.453076, 1.784999 14.23157, 1.732766 14.010053, 1.680625 13.788524, 1.628576 13.566984, -0.972481 14.136174, -0.92288 14.357915, -0.8732259999999999 14.579649, -0.823524 14.801376, -0.773787 15.023097, -0.723996 15.24481, -0.6741470000000001 15.466515, -0.624248 15.688213, -0.574308 15.909904, -0.524307 16.131586, -0.474244 16.35326, -0.424129 16.574925, -0.373965 16.796583, -0.323736 17.018232, -0.27344 17.239872, -0.22309 17.461503, -0.172684 17.683126, -0.122206 17.904738, -0.071657 18.126341, -0.021051 18.347936, 0.029618 18.56952, 0.080364 18.791094, 0.131188 19.012658, 0.182068 19.234212, 0.233022 19.455756, 0.284057 19.677289, 0.335176 19.898811, 0.386353 20.120323, 3.069561 19.544106))"
              }],
             "style": {
                 "stroke_color": "green",
                 "fill_color": "rgba(0,255,0,0.3)",
             }
             },
             {"id": str(playback_completeness_channel_2[2].event_uuid),
             "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:20.858708</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:26.355940</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.092</td></tr>" +
                          "<tr><td>Playback type</td><td>SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_PARTIAL.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
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

        returned_acquisition_geometries_received = self.driver.execute_script('return acquisition_geometries_received;')
        returned_acquisition_geometries_received.sort(key=lambda x:x["id"])
        assert acquisition_geometries_received == returned_acquisition_geometries_received

        acquisition_geometries_missing = [
            {"id": str(playback_completeness_channel_1[0].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:24.907236</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:35:33.728601</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.147</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_PARTIAL.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((3.199905 20.067599, 3.13488 19.806822, 3.070036 19.546021, 0.386797 20.122241, 0.447252 20.38343, 0.507821 20.644603, 3.199905 20.067599))"
              }],
             "style": {
                 "stroke_color": "red",
                 "fill_color": "rgba(255,0,0,0.3)",
             }
             },
            {"id": str(playback_completeness_channel_2[0].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:24.907236</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:35:33.760977</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.148</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_PARTIAL.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((3.199905 20.067599, 3.134641 19.805864, 3.069561 19.544106, 0.386353 20.120323, 0.44703 20.382471, 0.507821 20.644603, 3.199905 20.067599))"
              }],
             "style": {
                 "stroke_color": "red",
                 "fill_color": "rgba(255,0,0,0.3)",
             }
            }
        ]

        returned_acquisition_geometries_missing = self.driver.execute_script('return acquisition_geometries_missing;')
        returned_acquisition_geometries_missing.sort(key=lambda x:x["id"])
        assert acquisition_geometries_missing == returned_acquisition_geometries_missing

        station_reports_no_data = wait.until(EC.visibility_of_element_located((By.ID,"station-reports-no-reports")))

        assert station_reports_no_data

    def test_acquisition_only_nppf_orbpre_and_station_report(self):

        filename = "S2A_NPPF_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_STNACQ.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_station_acquisition_report.ingestion_station_acquisition_report", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        wait = WebDriverWait(self.driver,5);

        self.driver.get("http://localhost:5000/views/acquisition")

        functions.query(self.driver, wait, "S2A", start = "2018-07-24T00:00:00", stop = "2018-07-25T00:00:00", start_orbit = "16122", stop_orbit = "16123", table_details = True, map = True, station_reports = True)

        # Missing acquisitions table

        acquisition_missing_table = self.driver.find_element_by_id("acquisition-missing-table")

        number_of_elements = len(acquisition_missing_table.find_elements_by_xpath("tbody/tr"))

        assert number_of_elements == 4

        playback_status_1 = acquisition_missing_table.find_element_by_xpath("tbody/tr[last()]/td[5]")

        assert playback_status_1.text == "MISSING"

        playback_status_2 = acquisition_missing_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert playback_status_2.text == "MISSING"

        playback_status_3 = acquisition_missing_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert playback_status_3.text == "MISSING"

        playback_status_4 = acquisition_missing_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert playback_status_4.text == "MISSING"

        # Acquisition Scheduling Completeness table

        acquisition_details_table = self.driver.find_element_by_id("acquisition-details-table")

        number_of_elements = len(acquisition_details_table.find_elements_by_xpath("tbody/tr"))

        assert number_of_elements == 4

        playback_status_1 = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[5]")

        assert playback_status_1.text == "MISSING"

        playback_status_2 = acquisition_details_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert playback_status_2.text == "MISSING"

        playback_status_3 = acquisition_details_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert playback_status_3.text == "MISSING"

        playback_status_4 = acquisition_details_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert playback_status_4.text == "MISSING"

        # Acquisition Scheduling Completeness timeline

        original_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"=="})

        original_events.sort(key=lambda x:x.start)

        corrected_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_CORRECTION", "op":"=="})

        corrected_events.sort(key=lambda x:x.start)

        playback_completeness_channel_1 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_1", "op":"=="})

        playback_completeness_channel_1.sort(key=lambda x:x.start)

        playback_completeness_channel_2 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2", "op":"=="})

        playback_completeness_channel_2.sort(key=lambda x:x.start)

        acquisition_timeline_missing = [
            {"id": str(playback_completeness_channel_1[0].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-24T12:03:25.140258",
             "stop": "2018-07-24T12:14:48.025786",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:03:25.140258</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:14:48.025786</td></tr>" +
                          "<tr><td>Duration(m)</td><td>11.381</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-red"
             },
            {"id": str(playback_completeness_channel_2[0].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-24T12:03:25.140258",
             "stop": "2018-07-24T12:14:48.025786",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:03:25.140258</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:14:48.025786</td></tr>" +
                          "<tr><td>Duration(m)</td><td>11.381</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-red"
             },
            {"id": str(playback_completeness_channel_1[1].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-24T12:15:10.023123",
             "stop": "2018-07-24T12:15:10.023123",
             "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:15:10.023123</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:15:10.023123</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                          "<tr><td>Playback type</td><td>HKTM_SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "className": "fill-border-red"
            },
            {"id": str(playback_completeness_channel_2[1].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-24T12:15:10.023123",
             "stop": "2018-07-24T12:15:10.023123",
             "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:15:10.023123</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:15:10.023123</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                          "<tr><td>Playback type</td><td>HKTM_SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "className": "fill-border-red"
            },
           {"id": str(playback_completeness_channel_1[2].event_uuid),
            "group": "S2A",
            "timeline": "",
            "start": "2018-07-24T12:17:57.403836",
            "stop": "2018-07-24T12:28:40.906438",
             "tooltip": "<table border='1'>" +
                         "<tr><td>UUID</td><td>" + str(original_events[2].event_uuid) + "</td></tr>" +
                         "<tr><td>Satellite</td><td>S2A</td></tr>" +
                         "<tr><td>Orbit</td><td>16122</td></tr>" +
                         "<tr><td>Station</td><td></td></tr>" +
                         "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[2].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                         "<tr><td>Start</td><td>2018-07-24T12:17:57.403836</td></tr>" +
                         "<tr><td>Stop</td><td>2018-07-24T12:28:40.906438</td></tr>" +
                         "<tr><td>Duration(m)</td><td>10.725</td></tr>" +
                         "<tr><td>Playback type</td><td>REGULAR</td></tr>" +
                         "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                         "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                         '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[2].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                         "</table>",
           "className": "fill-border-red"
            },
           {"id": str(playback_completeness_channel_2[2].event_uuid),
            "group": "S2A",
            "timeline": "",
            "start": "2018-07-24T12:17:57.403836",
            "stop": "2018-07-24T12:28:40.906438",
             "tooltip": "<table border='1'>" +
                         "<tr><td>UUID</td><td>" + str(original_events[2].event_uuid) + "</td></tr>" +
                         "<tr><td>Satellite</td><td>S2A</td></tr>" +
                         "<tr><td>Orbit</td><td>16122</td></tr>" +
                         "<tr><td>Station</td><td></td></tr>" +
                         "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[2].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                         "<tr><td>Start</td><td>2018-07-24T12:17:57.403836</td></tr>" +
                         "<tr><td>Stop</td><td>2018-07-24T12:28:40.906438</td></tr>" +
                         "<tr><td>Duration(m)</td><td>10.725</td></tr>" +
                         "<tr><td>Playback type</td><td>REGULAR</td></tr>" +
                         "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                         "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                         '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[2].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                         "</table>",
           "className": "fill-border-red"
            },
           {"id": str(playback_completeness_channel_2[3].event_uuid),
            "group": "S2A",
            "timeline": "",
            "start": "2018-07-24T12:29:02.911137",
            "stop": "2018-07-24T12:29:02.911137",
            "tooltip": "<table border='1'>" +
                         "<tr><td>UUID</td><td>" + str(original_events[3].event_uuid) + "</td></tr>" +
                         "<tr><td>Satellite</td><td>S2A</td></tr>" +
                         "<tr><td>Orbit</td><td>16122</td></tr>" +
                         "<tr><td>Station</td><td></td></tr>" +
                         "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[3].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                         "<tr><td>Start</td><td>2018-07-24T12:29:02.911137</td></tr>" +
                         "<tr><td>Stop</td><td>2018-07-24T12:29:02.911137</td></tr>" +
                         "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                         "<tr><td>Playback type</td><td>SAD</td></tr>" +
                         "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                         "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                         '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[3].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                         "</table>",
             "className": "fill-border-red"
           }
        ]

        returned_missing_playbacks_timeline = self.driver.execute_script('return missing_playbacks_timeline;')
        returned_missing_playbacks_timeline.sort(key=lambda x:x["start"])
        assert acquisition_timeline_missing == returned_missing_playbacks_timeline

        # Acquisition Scheduling Completeness map

        corrected_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_CORRECTION", "op":"=="})

        corrected_events.sort(key=lambda x:x.start)
        
        acquisition_geometries_missing = [
            {"id": str(corrected_events[0].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:03:16.140258</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:14:57.025786</td></tr>" +
                          "<tr><td>Duration(m)</td><td>11.681</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((118.967881 74.15591999999999, 118.457749 74.32329799999999, 117.937152 74.489518, 117.40593 74.654562, 116.86376 74.81838, 116.310322 74.980924, 115.745361 75.142155, 115.168701 75.302055, 114.57993 75.46055, 113.978759 75.61759499999999, 113.364991 75.773163, 112.738298 75.92719700000001, 112.098325 76.079634, 111.444792 76.230422, 110.777528 76.379537, 110.096099 76.52689100000001, 109.400212 76.672426, 108.689661 76.816101, 107.964143 76.957853, 107.223309 77.097599, 106.466888 77.235277, 105.694757 77.37085399999999, 104.906514 77.504226, 104.101913 77.635319, 103.280795 77.764082, 102.44295 77.890441, 101.588103 78.014298, 100.716077 78.135576, 99.82685600000001 78.25423499999999, 98.920177 78.37015700000001, 97.99593299999999 78.483256, 97.054113 78.593468, 96.094695 78.700715, 95.11760200000001 78.80488699999999, 94.12286899999999 78.905895, 93.11069000000001 79.00369499999999, 92.081085 79.098164, 91.03421299999999 79.18921, 89.970336 79.27676200000001, 88.88975600000001 79.360748, 87.792726 79.441052, 86.679631 79.51759, 85.550994 79.590318, 84.407246 79.65912400000001, 83.24893 79.723923, 82.07669300000001 79.78465, 80.891243 79.841255, 79.693262 79.893632, 78.483548 79.941717, 77.263001 79.985484, 76.03249 80.024852, 74.792959 80.059755, 73.545423 80.090159, 72.29094600000001 80.116049, 71.03057800000001 80.137351, 69.76543700000001 80.15403499999999, 68.496678 80.166112, 67.22545 80.173547, 65.952985 80.17494600000001, 64.681229 80.168936, 63.408726 80.167885, 62.139405 80.15669699999999, 60.873499 80.140863, 59.612138 80.120439, 58.356442 80.095438, 57.107516 80.065878, 55.86641 80.031803, 54.63409 79.9933, 53.411567 79.95037499999999, 52.199758 79.90308400000001, 50.999489 79.851516, 49.81157 79.79572899999999, 48.636784 79.735771, 47.475821 79.671716, 46.329225 79.603685, 45.197651 79.53170900000001, 44.081615 79.455868, 42.981515 79.37626899999999, 41.897739 79.292996, 40.830681 79.206109, 39.780624 79.115697, 38.747682 79.021889, 37.732142 78.92473, 36.734144 78.824305, 35.753718 78.720721, 34.790889 78.614071, 33.845737 78.504413, 32.918231 78.391834, 32.008181 78.276456, 31.115601 78.158327, 30.24038 78.03752299999999, 29.382317 77.914141, 28.541198 77.788269, 27.716921 77.659958, 26.909275 77.52928199999999, 26.117907 77.396348, 25.342675 77.2612, 24.583348 77.123902, 23.839619 76.984534, 23.111151 76.843174, 22.397772 76.699862, 21.699197 76.554659, 21.015018 76.407653, 20.345024 76.258883, 19.688957 76.108397, 19.046484 75.956259, 18.417228 75.802539, 17.801012 75.647263, 17.197543 75.49048000000001, 16.606422 75.332261, 16.027422 75.172639, 15.460303 75.01164900000001, 14.904757 74.84934, 14.360406 74.68577399999999, 13.827103 74.520966, 13.304576 74.35495299999999, 12.792469 74.187794, 12.290561 74.019516, 11.798653 73.850143, 11.31648 73.67971199999999, 10.843682 73.508279, 10.380151 73.335848, 9.925655000000001 73.16245000000001, 9.479884 72.98813, 9.042636 72.812912, 8.613756 72.63681200000001, 8.193026 72.459857, 7.78011 72.28209699999999, 7.374944 72.10353000000001, 6.97733 71.92418000000001, 6.587009 71.744084, 6.203797 71.563261, 5.827581 71.381722, 5.458185 71.19948599999999, 5.095307 71.016597, 4.738908 70.833051, 4.38883 70.648866, 4.044857 70.46407000000001, 3.706822 70.278682, 3.374648 70.09270600000001, 3.048189 69.906159, 2.727192 69.719076, 2.411623 69.531453, 2.10136 69.34330300000001, 1.796227 69.15464900000001, 1.49607 68.965508, 1.200842 68.775882, 0.910425 68.585781, 0.624603 68.395236, 0.343346 68.204245, 0.066565 68.012815, -0.205884 67.820965, -0.474146 67.628711, -0.738242 67.43605100000001, -0.998268 67.24299499999999, -1.254407 67.04956799999999, -1.506689 66.855767, -1.755176 66.661599, -1.999982 66.46707600000001, -2.24125 66.272217, -2.478976 66.077015, -2.713242 65.88148, -2.9442 65.68563, -3.171881 65.48946599999999, -3.396327 65.292991, -3.617629 65.096215, -3.835924 64.89915499999999, -4.051192 64.70180499999999, -4.2635 64.50417, -4.472977 64.306268, -4.679656 64.108099, -4.883562 63.909665, -5.084765 63.710973, -5.283399 63.512039, -5.479432 63.312857, -5.67292 63.113431, -5.86397 62.913775, -6.052619 62.713891, -6.238876 62.513779, -6.422797 62.313444, -6.604513 62.112902, -6.783981 61.912146, -6.961247 61.711179, -7.136402 61.510013, -7.309487 61.308651, -7.480499 61.107091, -7.64948 60.905337, -7.816556 60.703405, -7.981682 60.501287, -8.144892 60.298985, -8.306265 60.096509, -8.465843 59.893864, -8.623616 59.691046, -8.779617 59.488058, -8.933958000000001 59.284914, -13.820356 60.135419, -13.693583 60.3427, -13.565503 60.549891, -13.435969 60.756977, -13.304952 60.963957, -13.172493 61.170835, -13.038546 61.377609, -12.903021 61.584271, -12.765885 61.790818, -12.627234 61.997261, -12.4869 62.203584, -12.344848 62.409786, -12.201105 62.61587, -12.055638 62.821835, -11.908336 63.02767, -11.759158 63.233373, -11.608197 63.438955, -11.455282 63.6444, -11.30036 63.849704, -11.143448 64.05486999999999, -10.984522 64.25989800000001, -10.823447 64.464775, -10.660174 64.669499, -10.494786 64.87408000000001, -10.327111 65.078501, -10.157078 65.282758, -9.984685000000001 65.486853, -9.809919000000001 65.690786, -9.632619999999999 65.894543, -9.452724999999999 66.098119, -9.270303 66.301524, -9.085183000000001 66.504744, -8.897269 66.707769, -8.706538 66.9106, -8.512987000000001 67.113241, -8.316423 67.31567200000001, -8.116769 67.517889, -7.914074 67.71990099999999, -7.708166 67.921691, -7.498919 68.123251, -7.286284 68.32457599999999, -7.070265 68.525674, -6.850632 68.72652100000001, -6.627286 68.92711, -6.400251 69.127449, -6.169354 69.327523, -5.934429 69.527317, -5.695393 69.726827, -5.452257 69.92606000000001, -5.204744 70.124989, -4.952728 70.323605, -4.6962 70.521912, -4.434978 70.719897, -4.168849 70.91754, -3.897688 71.11483200000001, -3.621507 71.311784, -3.339971 71.50836099999999, -3.052918 71.70455200000001, -2.760295 71.90035899999999, -2.461905 72.095767, -2.157477 72.290751, -1.84683 72.485298, -1.529969 72.679418, -1.206488 72.87307199999999, -0.876177 73.066242, -0.538925 73.258928, -0.19451 73.451111, 0.157414 73.64276099999999, 0.517092 73.833859, 0.884559 74.024413, 1.260288 74.214376, 1.644563 74.40372600000001, 2.037567 74.59245300000001, 2.439563 74.78054, 2.850993 74.967944, 3.272178 75.15464, 3.703232 75.34062900000001, 4.144694 75.52585999999999, 4.596947 75.71029900000001, 5.060275 75.893928, 5.534997 76.076724, 6.021674 76.25863099999999, 6.520726 76.439616, 7.032372 76.61967, 7.557234 76.798731, 8.095822 76.976752, 8.648543 77.153702, 9.215792 77.329551, 9.798273999999999 77.504226, 10.396529 77.677677, 11.010904 77.84988199999999, 11.642118 78.020768, 12.290829 78.190265, 12.957583 78.35832499999999, 13.642861 78.524907, 14.347522 78.689913, 15.07223 78.853272, 15.817467 79.014944, 16.584038 79.174834, 17.372737 79.332848, 18.184234 79.488911, 19.019067 79.642966, 19.878208 79.794881, 20.762396 79.94456, 21.672186 80.09193500000001, 22.608392 80.236886, 23.571843 80.379285, 24.56322 80.519023, 25.582989 80.656025, 26.632069 80.79011800000001, 27.711088 80.921173, 28.820472 81.049091, 29.960795 81.173727, 31.132644 81.29491400000001, 32.336402 81.412509, 33.572139 81.526419, 34.840322 81.63643399999999, 36.141051 81.74239900000001, 37.474181 81.844188, 38.839565 81.941641, 40.237013 82.034569, 41.666055 82.122811, 43.125848 82.206271, 44.615774 82.284733, 46.13482 82.358041, 47.68169 82.426074, 49.254962 82.488698, 50.853109 82.545737, 52.474305 82.597064, 54.116421 82.64262100000001, 55.777367 82.682244, 57.454769 82.715829, 59.14606 82.74332, 60.848566 82.764664, 62.559547 82.779763, 64.27846 82.781175, 65.99550499999999 82.789297, 67.71432 82.787408, 69.430048 82.777367, 71.13963 82.76107, 72.840243 82.738586, 74.52909099999999 82.709923, 76.20351700000001 82.67515400000001, 77.861098 82.63441899999999, 79.499444 82.587779, 81.116355 82.535329, 82.70988199999999 82.477206, 84.278333 82.41357499999999, 85.82001 82.34452400000001, 87.33353200000001 82.27019799999999, 88.81786099999999 82.190793, 90.271947 82.106436, 91.694941 82.017264, 93.08627300000001 81.92344799999999, 94.445661 81.82518899999999, 95.772642 81.722594, 97.067082 81.61582199999999, 98.32914599999999 81.50506799999999, 99.558893 81.39046999999999, 100.75646 81.27215700000001, 101.922203 81.15028599999999, 103.056746 81.02504399999999, 104.160331 80.89652100000001, 105.233499 80.764855, 106.277006 80.630208, 107.291445 80.492699, 108.277368 80.35242700000001, 109.23548 80.209515, 110.166758 80.064121, 111.071655 79.91630499999999, 111.950907 79.766172, 112.8054 79.61384700000001, 113.635864 79.459424, 114.442893 79.302969, 115.227214 79.144572, 115.989822 78.98436, 116.731147 78.822368, 117.451877 78.658671, 118.152813 78.493362, 118.834644 78.32651199999999, 119.497858 78.158164, 120.143082 77.98838000000001, 120.771176 77.817257, 121.382499 77.644818, 121.977601 77.471114, 122.557139 77.29621, 123.121707 77.120164, 123.671658 76.943, 124.207491 76.764762, 124.72991 76.58552299999999, 125.239195 76.405298, 125.735756 76.224119, 126.220103 76.042036, 126.692745 75.859094, 127.153909 75.675304, 118.967881 74.15591999999999))"
              }],
             "style": {
                 "stroke_color": "red",
                 "fill_color": "rgba(255,0,0,0.3)",
             }
             },
             {"id": str(corrected_events[1].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:15:08.023123</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:15:08.023123</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                          "<tr><td>Playback type</td><td>HKTM_SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                  "value": "POLYGON ((-9.393459 58.665562, -14.197858 59.503855, -14.197858 59.503855, -9.393459 58.665562))"
              }],
              "style": {
                  "stroke_color": "red",
                  "fill_color": "rgba(255,0,0,0.3)",
              }
            },
            {"id": str(corrected_events[2].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[2].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[2].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:17:48.403836</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:28:49.906438</td></tr>" +
                          "<tr><td>Duration(m)</td><td>11.025</td></tr>" +
                          "<tr><td>Playback type</td><td>REGULAR</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((-14.766859 49.505215, -14.866248 49.29662, -14.964886 49.08795, -15.062805 48.879207, -15.160032 48.670394, -15.256541 48.461509, -15.352344 48.252551, -15.447495 48.043528, -15.541969 47.834435, -15.635768 47.625274, -15.728915 47.416046, -15.821445 47.206755, -15.913327 46.997398, -16.004572 46.787975, -16.095226 46.578491, -16.185275 46.368945, -16.274714 46.159336, -16.36356 45.949665, -16.451854 45.739937, -16.539563 45.530148, -16.626695 45.3203, -16.713291 45.110395, -16.799343 44.900433, -16.884842 44.690414, -16.969802 44.480338, -17.054266 44.270209, -17.1382 44.060025, -17.221612 43.849785, -17.304534 43.639494, -17.386968 43.42915, -17.468899 43.218754, -17.550338 43.008305, -17.631332 42.797808, -17.711844 42.58726, -17.791881 42.376661, -17.871471 42.166014, -17.95062 41.955319, -18.029313 41.744575, -18.107556 41.533783, -18.185396 41.322946, -18.262798 41.112062, -18.339768 40.901131, -18.416329 40.690156, -18.492492 40.479136, -18.568239 40.268071, -18.643575 40.056962, -18.718542 39.845811, -18.793113 39.634617, -18.86729 39.423379, -18.941091 39.2121, -19.014532 39.00078, -19.087593 38.789418, -19.16028 38.578015, -19.232627 38.366574, -19.304616 38.155092, -19.376244 37.94357, -19.447526 37.732009, -19.518483 37.520411, -19.589092 37.308774, -19.659359 37.097099, -19.729313 36.885387, -19.798942 36.673638, -19.86824 36.461853, -19.93722 36.250031, -20.005905 36.038174, -20.074272 35.826281, -20.142325 35.614353, -20.21009 35.402391, -20.277559 35.190394, -20.344726 34.978363, -20.411599 34.766298, -20.478204 34.554201, -20.544517 34.342071, -20.610543 34.129907, -20.676302 33.917712, -20.741793 33.705485, -20.807006 33.493226, -20.871947 33.280936, -20.936645 33.068615, -21.001075 32.856263, -21.065242 32.643881, -21.129162 32.431469, -21.192838 32.219028, -21.256258 32.006557, -21.319428 31.794056, -21.382376 31.581527, -21.445078 31.36897, -21.507538 31.156384, -21.569769 30.94377, -21.631779 30.731129, -21.693554 30.51846, -21.755098 30.305764, -21.816437 30.093042, -21.877552 29.880293, -21.938444 29.667517, -21.999125 29.454716, -22.059603 29.241889, -22.119866 29.029036, -22.179917 28.816158, -22.239777 28.603255, -22.299433 28.390328, -22.358884 28.177376, -22.41814 27.9644, -22.477211 27.7514, -22.536084 27.538377, -22.594761 27.32533, -22.653262 27.112259, -22.711577 26.899166, -22.769704 26.686051, -22.827649 26.472912, -22.885426 26.259752, -22.94302 26.046569, -23.000436 25.833365, -23.057687 25.620139, -23.114769 25.406893, -23.171677 25.193625, -23.228418 24.980336, -23.285005 24.767026, -23.341424 24.553697, -23.397679 24.340347, -23.453781 24.126977, -23.509729 23.913587, -23.565518 23.700178, -23.621152 23.48675, -23.676644 23.273303, -23.731984 23.059836, -23.787172 22.846351, -23.842219 22.632848, -23.897125 22.419327, -23.951885 22.205788, -24.006501 21.99223, -24.060989 21.778656, -24.115337 21.565064, -24.169545 21.351454, -24.223623 21.137828, -24.277572 20.924185, -24.331388 20.710526, -24.385071 20.49685, -24.438636 20.283158, -24.492073 20.06945, -24.545382 19.855726, -24.598571 19.641987, -24.651643 19.428232, -24.704592 19.214462, -24.757421 19.000678, -24.81014 18.786878, -24.862742 18.573064, -24.915228 18.359235, -24.967603 18.145393, -25.019871 17.931536, -25.072028 17.717665, -25.124074 17.503781, -25.176018 17.289884, -25.227858 17.075973, -25.279591 16.862049, -25.331222 16.648112, -25.382755 16.434162, -25.434188 16.2202, -25.48552 16.006226, -25.536758 15.792239, -25.5879 15.578241, -25.638947 15.36423, -25.689899 15.150208, -25.740764 14.936175, -25.791536 14.72213, -25.842218 14.508074, -25.892813 14.294008, -25.943322 14.07993, -25.993744 13.865842, -26.044081 13.651744, -26.094338 13.437635, -26.144511 13.223517, -26.194602 13.009388, -26.244615 12.79525, -26.29455 12.581103, -26.344407 12.366946, -26.394186 12.15278, -26.443893 11.938605, -26.493525 11.724421, -26.543084 11.510228, -26.592571 11.296027, -26.641988 11.081818, -26.691335 10.867601, -26.740614 10.653375, -29.313131 11.22025, -29.265678 11.43462, -29.218189 11.648984, -29.170663 11.863344, -29.123112 12.077699, -29.075534 12.292051, -29.027915 12.506396, -28.980256 12.720736, -28.93258 12.935072, -28.88486 13.149402, -28.837097 13.363726, -28.7893 13.578045, -28.741471 13.792359, -28.693594 14.006666, -28.645669 14.220966, -28.597719 14.435261, -28.549721 14.649549, -28.50167 14.863831, -28.453578 15.078106, -28.405448 15.292374, -28.357263 15.506635, -28.309022 15.720889, -28.260748 15.935136, -28.212419 16.149375, -28.164031 16.363607, -28.115591 16.57783, -28.067109 16.792047, -28.018564 17.006255, -27.969955 17.220454, -27.921303 17.434646, -27.872592 17.64883, -27.823812 17.863004, -27.77497 18.077169, -27.726082 18.291326, -27.677123 18.505474, -27.62809 18.719612, -27.579005 18.933742, -27.529855 19.147862, -27.480628 19.361972, -27.431328 19.576071, -27.381976 19.790162, -27.332544 20.004242, -27.28303 20.218312, -27.233454 20.432372, -27.183806 20.646421, -27.134072 20.860459, -27.084254 21.074486, -27.034379 21.288503, -26.984414 21.502508, -26.934357 21.716502, -26.884227 21.930484, -26.83402 22.144455, -26.783716 22.358414, -26.733315 22.572361, -26.682853 22.786297, -26.632291 23.00022, -26.581626 23.21413, -26.530877 23.428028, -26.480043 23.641914, -26.429103 23.855786, -26.378055 24.069645, -26.326935 24.283492, -26.275706 24.497325, -26.224365 24.711144, -26.172925 24.92495, -26.121395 25.138743, -26.069747 25.352521, -26.017979 25.566285, -25.966127 25.780035, -25.914158 25.993771, -25.862066 26.207491, -25.809861 26.421197, -25.757557 26.634889, -25.705124 26.848566, -25.65256 27.062226, -25.599897 27.275872, -25.547109 27.489503, -25.494185 27.703117, -25.441133 27.916715, -25.387975 28.130298, -25.334674 28.343864, -25.281229 28.557413, -25.227671 28.770947, -25.173978 28.984464, -25.120136 29.197964, -25.066149 29.411446, -25.012047 29.624912, -24.957789 29.83836, -24.903373 30.05179, -24.848827 30.265203, -24.794137 30.478598, -24.739282 30.691975, -24.684265 30.905333, -24.629123 31.118674, -24.573811 31.331995, -24.518325 31.545297, -24.462691 31.758581, -24.406902 31.971845, -24.350933 32.18509, -24.294781 32.398315, -24.238495 32.611521, -24.182022 32.824707, -24.125359 33.037872, -24.068528 33.251017, -24.01153 33.464143, -23.954334 33.677247, -23.896937 33.890329, -23.839389 34.103392, -23.781639 34.316433, -23.72368 34.529451, -23.665532 34.742449, -23.607203 34.955425, -23.548658 35.168378, -23.489893 35.381308, -23.430956 35.594218, -23.3718 35.807104, -23.312416 36.019966, -23.252819 36.232806, -23.193027 36.445623, -23.132998 36.658416, -23.072727 36.871183, -23.01226 37.083929, -22.951558 37.29665, -22.890606 37.509345, -22.829415 37.722016, -22.768012 37.934663, -22.706349 38.147284, -22.644421 38.359878, -22.58227 38.572449, -22.519866 38.784993, -22.457186 38.99751, -22.394239 39.21, -22.331062 39.422466, -22.267599 39.634903, -22.203845 39.847312, -22.139839 40.059695, -22.075558 40.272051, -22.010975 40.484377, -21.946093 40.696675, -21.88096 40.908946, -21.815511 41.121187, -21.749744 41.333398, -21.683692 41.545581, -21.617341 41.757734, -21.550657 41.969857, -21.483638 42.181947, -21.416345 42.394011, -21.348705 42.606042, -21.280713 42.81804, -21.2124 43.030008, -21.143762 43.241945, -21.074757 43.453848, -21.005379 43.665718, -20.935694 43.877557, -20.865631 44.089363, -20.795178 44.301133, -20.724363 44.51287, -20.653193 44.724574, -20.581617 44.936242, -20.50963 45.147874, -20.437293 45.359473, -20.364543 45.571036, -20.291363 45.782561, -20.217774 45.994049, -20.143795 46.205503, -20.069368 46.416917, -19.994484 46.628292, -19.919204 46.839632, -19.84347 47.050933, -19.76726 47.262192, -19.690589 47.473412, -19.613488 47.684595, -19.535888 47.895736, -19.457783 48.106833, -19.379226 48.317892, -19.300171 48.528909, -19.220587 48.739882, -19.140481 48.950811, -19.0599 49.1617, -18.978764 49.372543, -18.897065 49.58334, -18.814852 49.794094, -18.732089 50.004803, -18.648736 50.215463, -14.766859 49.505215))"
              }],
             "style": {
                 "stroke_color": "red",
                 "fill_color": "rgba(255,0,0,0.3)",
             }
             },
             {"id": str(corrected_events[3].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[3].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[3].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:29:00.911137</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:29:00.911137</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                          "<tr><td>Playback type</td><td>SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                  "value": "POLYGON ((-26.890228 10.001146, -29.457458 10.567606, -29.457458 10.567606, -26.890228 10.001146))"
              }],
              "style": {
                  "stroke_color": "red",
                  "fill_color": "rgba(255,0,0,0.3)",
              }
            }
        ]

        returned_acquisition_geometries_missing = self.driver.execute_script('return acquisition_geometries_missing;')
        returned_acquisition_geometries_missing.sort(key=lambda x:x["id"])

        # Station Reports table

        station_reports_table = self.driver.find_element_by_id("station-acquisition-reports-table")

        satellite = station_reports_table.find_element_by_xpath("tbody/tr[last()]/td[1]")

        assert satellite.text == "S2A"

        orbit = station_reports_table.find_element_by_xpath("tbody/tr[last()]/td[2]")

        assert orbit.text == "16122"

        station = station_reports_table.find_element_by_xpath("tbody/tr[last()]/td[3]")

        assert station.text == "MPS_"

        antenna_id = station_reports_table.find_element_by_xpath("tbody/tr[last()]/td[4]")

        assert antenna_id.text == "MSP21"

        status = station_reports_table.find_element_by_xpath("tbody/tr[last()]/td[5]")

        assert status.text == "OK"

        comments = station_reports_table.find_element_by_xpath("tbody/tr[last()]/td[6]")

        assert comments.text == ""

        start = station_reports_table.find_element_by_xpath("tbody/tr[last()]/td[7]")

        assert start.text == "2018-07-24 12:17:23"

        stop = station_reports_table.find_element_by_xpath("tbody/tr[last()]/td[8]")

        assert stop.text == "2018-07-24 12:29:32"

        source = station_reports_table.find_element_by_xpath("tbody/tr[last()]/td[9]")

        assert source.text == "S2A_STNACQ.EOF"

        uuid = station_reports_table.find_element_by_xpath("tbody/tr[last()]/td[10]")

        assert re.match("........-....-....-....-............", uuid.text)

    def test_acquisition_mixing_received_and_missing(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_MPL_SPMPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_REP_PASS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_NPPF_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_STNACQ.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_station_acquisition_report.ingestion_station_acquisition_report", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        wait = WebDriverWait(self.driver,5);

        self.driver.get("http://localhost:5000/views/acquisition")

        functions.query(self.driver, wait, "S2A", start = "2018-07-21T00:00:00", stop = "2018-07-25T00:00:00", start_orbit = "16078", stop_orbit = "16123", table_details = True, map = True, station_reports = True)

        # Missing acquisitions table

        acquisition_missing_table = self.driver.find_element_by_id("acquisition-missing-table")

        number_of_elements = len(acquisition_missing_table.find_elements_by_xpath("tbody/tr"))

        assert number_of_elements == 4

        playback_status_1 = acquisition_missing_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert playback_status_1.text == "MISSING"

        playback_status_2 = acquisition_missing_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert playback_status_2.text == "MISSING"

        playback_status_3 = acquisition_missing_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert playback_status_3.text == "MISSING"

        playback_status_4 = acquisition_missing_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert playback_status_4.text == "MISSING"

        # Acquisition Scheduling Completeness table

        acquisition_details_table = self.driver.find_element_by_id("acquisition-details-table")

        number_of_elements = len(acquisition_details_table.find_elements_by_xpath("tbody/tr"))

        assert number_of_elements == 6

        playback_status_1 = acquisition_details_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert playback_status_1.text == "MISSING"

        playback_status_2 = acquisition_details_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert playback_status_2.text == "MISSING"

        playback_status_3 = acquisition_details_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert playback_status_3.text == "MISSING"

        playback_status_4 = acquisition_details_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert playback_status_4.text == "MISSING"

        playback_status_5 = acquisition_details_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert playback_status_5.text == "RECEIVED"

        playback_status_6 = acquisition_details_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert playback_status_6.text == "RECEIVED"

        # Acquisition Scheduling Completeness timeline

        original_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"=="})

        original_events.sort(key=lambda x:x.start)

        corrected_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_CORRECTION", "op":"=="})

        corrected_events.sort(key=lambda x:x.start)

        playback_completeness_channel_1 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_1", "op":"=="})

        playback_completeness_channel_1.sort(key=lambda x:x.start)

        playback_completeness_channel_2 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2", "op":"=="})

        playback_completeness_channel_2.sort(key=lambda x:x.start)

        acquisition_timeline_received = [
            {"id": str(playback_completeness_channel_1[0].event_uuid),
             "group": "S2A",
             "timeline": "MPS_",
             "start": "2018-07-21T10:35:33.728601",
             "stop": "2018-07-21T10:37:14.719834",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td>MPS_</td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.728601</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.719834</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-green"
             },
            {"id": str(playback_completeness_channel_2[0].event_uuid),
             "group": "S2A",
             "timeline": "MPS_",
             "start": "2018-07-21T10:35:33.760977",
             "stop": "2018-07-21T10:37:14.753003",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td>MPS_</td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.760977</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.753003</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-green"
             },
            {"id": str(playback_completeness_channel_2[1].event_uuid),
             "group": "S2A",
             "timeline": "MPS_",
             "start": "2018-07-21T10:37:20.858708",
             "stop": "2018-07-21T10:37:26.355940",
             "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td>MPS_</td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:20.858708</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:26.355940</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.092</td></tr>" +
                          "<tr><td>Playback type</td><td>SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "className": "fill-border-green"
            }
        ]

        returned_received_playbacks_timeline = self.driver.execute_script('return received_playbacks_timeline;')
        returned_received_playbacks_timeline.sort(key=lambda x:x["start"])
        assert acquisition_timeline_received == returned_received_playbacks_timeline

        acquisition_timeline_missing = [
            {"id": str(playback_completeness_channel_1[1].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-24T12:03:25.140258",
             "stop": "2018-07-24T12:14:48.025786",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[2].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[2].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:03:25.140258</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:14:48.025786</td></tr>" +
                          "<tr><td>Duration(m)</td><td>11.381</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[2].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
             "className": "fill-border-red"
             },
            {"id": str(playback_completeness_channel_2[2].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-24T12:03:25.140258",
             "stop": "2018-07-24T12:14:48.025786",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[2].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[2].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:03:25.140258</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:14:48.025786</td></tr>" +
                          "<tr><td>Duration(m)</td><td>11.381</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[2].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
             "className": "fill-border-red"
            },
            {"id": str(playback_completeness_channel_1[2].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-24T12:15:10.023123",
             "stop": "2018-07-24T12:15:10.023123",
             "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[3].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[3].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:15:10.023123</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:15:10.023123</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                          "<tr><td>Playback type</td><td>HKTM_SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[3].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "className": "fill-border-red"
            },
            {"id": str(playback_completeness_channel_2[3].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-24T12:15:10.023123",
             "stop": "2018-07-24T12:15:10.023123",
             "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[3].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[3].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:15:10.023123</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:15:10.023123</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                          "<tr><td>Playback type</td><td>HKTM_SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[3].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "className": "fill-border-red"
            },
           {"id": str(playback_completeness_channel_1[3].event_uuid),
            "group": "S2A",
            "timeline": "",
            "start": "2018-07-24T12:17:57.403836",
            "stop": "2018-07-24T12:28:40.906438",
             "tooltip": "<table border='1'>" +
                         "<tr><td>UUID</td><td>" + str(original_events[4].event_uuid) + "</td></tr>" +
                         "<tr><td>Satellite</td><td>S2A</td></tr>" +
                         "<tr><td>Orbit</td><td>16122</td></tr>" +
                         "<tr><td>Station</td><td></td></tr>" +
                         "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[4].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                         "<tr><td>Start</td><td>2018-07-24T12:17:57.403836</td></tr>" +
                         "<tr><td>Stop</td><td>2018-07-24T12:28:40.906438</td></tr>" +
                         "<tr><td>Duration(m)</td><td>10.725</td></tr>" +
                         "<tr><td>Playback type</td><td>REGULAR</td></tr>" +
                         "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                         "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                         '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[4].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                         "</table>",
           "className": "fill-border-red"
            },
           {"id": str(playback_completeness_channel_2[4].event_uuid),
            "group": "S2A",
            "timeline": "",
            "start": "2018-07-24T12:17:57.403836",
            "stop": "2018-07-24T12:28:40.906438",
             "tooltip": "<table border='1'>" +
                         "<tr><td>UUID</td><td>" + str(original_events[4].event_uuid) + "</td></tr>" +
                         "<tr><td>Satellite</td><td>S2A</td></tr>" +
                         "<tr><td>Orbit</td><td>16122</td></tr>" +
                         "<tr><td>Station</td><td></td></tr>" +
                         "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[4].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                         "<tr><td>Start</td><td>2018-07-24T12:17:57.403836</td></tr>" +
                         "<tr><td>Stop</td><td>2018-07-24T12:28:40.906438</td></tr>" +
                         "<tr><td>Duration(m)</td><td>10.725</td></tr>" +
                         "<tr><td>Playback type</td><td>REGULAR</td></tr>" +
                         "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                         "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                         '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[4].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                         "</table>",
           "className": "fill-border-red"
            },
           {"id": str(playback_completeness_channel_2[5].event_uuid),
            "group": "S2A",
            "timeline": "",
            "start": "2018-07-24T12:29:02.911137",
            "stop": "2018-07-24T12:29:02.911137",
            "tooltip": "<table border='1'>" +
                         "<tr><td>UUID</td><td>" + str(original_events[5].event_uuid) + "</td></tr>" +
                         "<tr><td>Satellite</td><td>S2A</td></tr>" +
                         "<tr><td>Orbit</td><td>16122</td></tr>" +
                         "<tr><td>Station</td><td></td></tr>" +
                         "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[5].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                         "<tr><td>Start</td><td>2018-07-24T12:29:02.911137</td></tr>" +
                         "<tr><td>Stop</td><td>2018-07-24T12:29:02.911137</td></tr>" +
                         "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                         "<tr><td>Playback type</td><td>SAD</td></tr>" +
                         "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                         "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                         '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[5].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                         "</table>",
             "className": "fill-border-red"
           }
        ]

        returned_missing_playbacks_timeline = self.driver.execute_script('return missing_playbacks_timeline;')
        returned_missing_playbacks_timeline.sort(key=lambda x:x["start"])
        assert acquisition_timeline_missing == returned_missing_playbacks_timeline

        # Acquisition Scheduling Completeness map

        acquisition_geometries_missing = [
            {"id": str(corrected_events[0].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:03:16.140258</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:14:57.025786</td></tr>" +
                          "<tr><td>Duration(m)</td><td>11.681</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((118.967881 74.15591999999999, 118.457749 74.32329799999999, 117.937152 74.489518, 117.40593 74.654562, 116.86376 74.81838, 116.310322 74.980924, 115.745361 75.142155, 115.168701 75.302055, 114.57993 75.46055, 113.978759 75.61759499999999, 113.364991 75.773163, 112.738298 75.92719700000001, 112.098325 76.079634, 111.444792 76.230422, 110.777528 76.379537, 110.096099 76.52689100000001, 109.400212 76.672426, 108.689661 76.816101, 107.964143 76.957853, 107.223309 77.097599, 106.466888 77.235277, 105.694757 77.37085399999999, 104.906514 77.504226, 104.101913 77.635319, 103.280795 77.764082, 102.44295 77.890441, 101.588103 78.014298, 100.716077 78.135576, 99.82685600000001 78.25423499999999, 98.920177 78.37015700000001, 97.99593299999999 78.483256, 97.054113 78.593468, 96.094695 78.700715, 95.11760200000001 78.80488699999999, 94.12286899999999 78.905895, 93.11069000000001 79.00369499999999, 92.081085 79.098164, 91.03421299999999 79.18921, 89.970336 79.27676200000001, 88.88975600000001 79.360748, 87.792726 79.441052, 86.679631 79.51759, 85.550994 79.590318, 84.407246 79.65912400000001, 83.24893 79.723923, 82.07669300000001 79.78465, 80.891243 79.841255, 79.693262 79.893632, 78.483548 79.941717, 77.263001 79.985484, 76.03249 80.024852, 74.792959 80.059755, 73.545423 80.090159, 72.29094600000001 80.116049, 71.03057800000001 80.137351, 69.76543700000001 80.15403499999999, 68.496678 80.166112, 67.22545 80.173547, 65.952985 80.17494600000001, 64.681229 80.168936, 63.408726 80.167885, 62.139405 80.15669699999999, 60.873499 80.140863, 59.612138 80.120439, 58.356442 80.095438, 57.107516 80.065878, 55.86641 80.031803, 54.63409 79.9933, 53.411567 79.95037499999999, 52.199758 79.90308400000001, 50.999489 79.851516, 49.81157 79.79572899999999, 48.636784 79.735771, 47.475821 79.671716, 46.329225 79.603685, 45.197651 79.53170900000001, 44.081615 79.455868, 42.981515 79.37626899999999, 41.897739 79.292996, 40.830681 79.206109, 39.780624 79.115697, 38.747682 79.021889, 37.732142 78.92473, 36.734144 78.824305, 35.753718 78.720721, 34.790889 78.614071, 33.845737 78.504413, 32.918231 78.391834, 32.008181 78.276456, 31.115601 78.158327, 30.24038 78.03752299999999, 29.382317 77.914141, 28.541198 77.788269, 27.716921 77.659958, 26.909275 77.52928199999999, 26.117907 77.396348, 25.342675 77.2612, 24.583348 77.123902, 23.839619 76.984534, 23.111151 76.843174, 22.397772 76.699862, 21.699197 76.554659, 21.015018 76.407653, 20.345024 76.258883, 19.688957 76.108397, 19.046484 75.956259, 18.417228 75.802539, 17.801012 75.647263, 17.197543 75.49048000000001, 16.606422 75.332261, 16.027422 75.172639, 15.460303 75.01164900000001, 14.904757 74.84934, 14.360406 74.68577399999999, 13.827103 74.520966, 13.304576 74.35495299999999, 12.792469 74.187794, 12.290561 74.019516, 11.798653 73.850143, 11.31648 73.67971199999999, 10.843682 73.508279, 10.380151 73.335848, 9.925655000000001 73.16245000000001, 9.479884 72.98813, 9.042636 72.812912, 8.613756 72.63681200000001, 8.193026 72.459857, 7.78011 72.28209699999999, 7.374944 72.10353000000001, 6.97733 71.92418000000001, 6.587009 71.744084, 6.203797 71.563261, 5.827581 71.381722, 5.458185 71.19948599999999, 5.095307 71.016597, 4.738908 70.833051, 4.38883 70.648866, 4.044857 70.46407000000001, 3.706822 70.278682, 3.374648 70.09270600000001, 3.048189 69.906159, 2.727192 69.719076, 2.411623 69.531453, 2.10136 69.34330300000001, 1.796227 69.15464900000001, 1.49607 68.965508, 1.200842 68.775882, 0.910425 68.585781, 0.624603 68.395236, 0.343346 68.204245, 0.066565 68.012815, -0.205884 67.820965, -0.474146 67.628711, -0.738242 67.43605100000001, -0.998268 67.24299499999999, -1.254407 67.04956799999999, -1.506689 66.855767, -1.755176 66.661599, -1.999982 66.46707600000001, -2.24125 66.272217, -2.478976 66.077015, -2.713242 65.88148, -2.9442 65.68563, -3.171881 65.48946599999999, -3.396327 65.292991, -3.617629 65.096215, -3.835924 64.89915499999999, -4.051192 64.70180499999999, -4.2635 64.50417, -4.472977 64.306268, -4.679656 64.108099, -4.883562 63.909665, -5.084765 63.710973, -5.283399 63.512039, -5.479432 63.312857, -5.67292 63.113431, -5.86397 62.913775, -6.052619 62.713891, -6.238876 62.513779, -6.422797 62.313444, -6.604513 62.112902, -6.783981 61.912146, -6.961247 61.711179, -7.136402 61.510013, -7.309487 61.308651, -7.480499 61.107091, -7.64948 60.905337, -7.816556 60.703405, -7.981682 60.501287, -8.144892 60.298985, -8.306265 60.096509, -8.465843 59.893864, -8.623616 59.691046, -8.779617 59.488058, -8.933958000000001 59.284914, -13.820356 60.135419, -13.693583 60.3427, -13.565503 60.549891, -13.435969 60.756977, -13.304952 60.963957, -13.172493 61.170835, -13.038546 61.377609, -12.903021 61.584271, -12.765885 61.790818, -12.627234 61.997261, -12.4869 62.203584, -12.344848 62.409786, -12.201105 62.61587, -12.055638 62.821835, -11.908336 63.02767, -11.759158 63.233373, -11.608197 63.438955, -11.455282 63.6444, -11.30036 63.849704, -11.143448 64.05486999999999, -10.984522 64.25989800000001, -10.823447 64.464775, -10.660174 64.669499, -10.494786 64.87408000000001, -10.327111 65.078501, -10.157078 65.282758, -9.984685000000001 65.486853, -9.809919000000001 65.690786, -9.632619999999999 65.894543, -9.452724999999999 66.098119, -9.270303 66.301524, -9.085183000000001 66.504744, -8.897269 66.707769, -8.706538 66.9106, -8.512987000000001 67.113241, -8.316423 67.31567200000001, -8.116769 67.517889, -7.914074 67.71990099999999, -7.708166 67.921691, -7.498919 68.123251, -7.286284 68.32457599999999, -7.070265 68.525674, -6.850632 68.72652100000001, -6.627286 68.92711, -6.400251 69.127449, -6.169354 69.327523, -5.934429 69.527317, -5.695393 69.726827, -5.452257 69.92606000000001, -5.204744 70.124989, -4.952728 70.323605, -4.6962 70.521912, -4.434978 70.719897, -4.168849 70.91754, -3.897688 71.11483200000001, -3.621507 71.311784, -3.339971 71.50836099999999, -3.052918 71.70455200000001, -2.760295 71.90035899999999, -2.461905 72.095767, -2.157477 72.290751, -1.84683 72.485298, -1.529969 72.679418, -1.206488 72.87307199999999, -0.876177 73.066242, -0.538925 73.258928, -0.19451 73.451111, 0.157414 73.64276099999999, 0.517092 73.833859, 0.884559 74.024413, 1.260288 74.214376, 1.644563 74.40372600000001, 2.037567 74.59245300000001, 2.439563 74.78054, 2.850993 74.967944, 3.272178 75.15464, 3.703232 75.34062900000001, 4.144694 75.52585999999999, 4.596947 75.71029900000001, 5.060275 75.893928, 5.534997 76.076724, 6.021674 76.25863099999999, 6.520726 76.439616, 7.032372 76.61967, 7.557234 76.798731, 8.095822 76.976752, 8.648543 77.153702, 9.215792 77.329551, 9.798273999999999 77.504226, 10.396529 77.677677, 11.010904 77.84988199999999, 11.642118 78.020768, 12.290829 78.190265, 12.957583 78.35832499999999, 13.642861 78.524907, 14.347522 78.689913, 15.07223 78.853272, 15.817467 79.014944, 16.584038 79.174834, 17.372737 79.332848, 18.184234 79.488911, 19.019067 79.642966, 19.878208 79.794881, 20.762396 79.94456, 21.672186 80.09193500000001, 22.608392 80.236886, 23.571843 80.379285, 24.56322 80.519023, 25.582989 80.656025, 26.632069 80.79011800000001, 27.711088 80.921173, 28.820472 81.049091, 29.960795 81.173727, 31.132644 81.29491400000001, 32.336402 81.412509, 33.572139 81.526419, 34.840322 81.63643399999999, 36.141051 81.74239900000001, 37.474181 81.844188, 38.839565 81.941641, 40.237013 82.034569, 41.666055 82.122811, 43.125848 82.206271, 44.615774 82.284733, 46.13482 82.358041, 47.68169 82.426074, 49.254962 82.488698, 50.853109 82.545737, 52.474305 82.597064, 54.116421 82.64262100000001, 55.777367 82.682244, 57.454769 82.715829, 59.14606 82.74332, 60.848566 82.764664, 62.559547 82.779763, 64.27846 82.781175, 65.99550499999999 82.789297, 67.71432 82.787408, 69.430048 82.777367, 71.13963 82.76107, 72.840243 82.738586, 74.52909099999999 82.709923, 76.20351700000001 82.67515400000001, 77.861098 82.63441899999999, 79.499444 82.587779, 81.116355 82.535329, 82.70988199999999 82.477206, 84.278333 82.41357499999999, 85.82001 82.34452400000001, 87.33353200000001 82.27019799999999, 88.81786099999999 82.190793, 90.271947 82.106436, 91.694941 82.017264, 93.08627300000001 81.92344799999999, 94.445661 81.82518899999999, 95.772642 81.722594, 97.067082 81.61582199999999, 98.32914599999999 81.50506799999999, 99.558893 81.39046999999999, 100.75646 81.27215700000001, 101.922203 81.15028599999999, 103.056746 81.02504399999999, 104.160331 80.89652100000001, 105.233499 80.764855, 106.277006 80.630208, 107.291445 80.492699, 108.277368 80.35242700000001, 109.23548 80.209515, 110.166758 80.064121, 111.071655 79.91630499999999, 111.950907 79.766172, 112.8054 79.61384700000001, 113.635864 79.459424, 114.442893 79.302969, 115.227214 79.144572, 115.989822 78.98436, 116.731147 78.822368, 117.451877 78.658671, 118.152813 78.493362, 118.834644 78.32651199999999, 119.497858 78.158164, 120.143082 77.98838000000001, 120.771176 77.817257, 121.382499 77.644818, 121.977601 77.471114, 122.557139 77.29621, 123.121707 77.120164, 123.671658 76.943, 124.207491 76.764762, 124.72991 76.58552299999999, 125.239195 76.405298, 125.735756 76.224119, 126.220103 76.042036, 126.692745 75.859094, 127.153909 75.675304, 118.967881 74.15591999999999))"
              }],
             "style": {
                 "stroke_color": "red",
                 "fill_color": "rgba(255,0,0,0.3)",
             }
             },
             {"id": str(corrected_events[1].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:15:08.023123</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:15:08.023123</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                          "<tr><td>Playback type</td><td>HKTM_SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                  "value": "POLYGON ((-9.393459 58.665562, -14.197858 59.503855, -14.197858 59.503855, -9.393459 58.665562))"
              }],
              "style": {
                  "stroke_color": "red",
                  "fill_color": "rgba(255,0,0,0.3)",
              }
            },
            {"id": str(corrected_events[2].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[2].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[2].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:17:48.403836</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:28:49.906438</td></tr>" +
                          "<tr><td>Duration(m)</td><td>11.025</td></tr>" +
                          "<tr><td>Playback type</td><td>REGULAR</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((-14.766859 49.505215, -14.866248 49.29662, -14.964886 49.08795, -15.062805 48.879207, -15.160032 48.670394, -15.256541 48.461509, -15.352344 48.252551, -15.447495 48.043528, -15.541969 47.834435, -15.635768 47.625274, -15.728915 47.416046, -15.821445 47.206755, -15.913327 46.997398, -16.004572 46.787975, -16.095226 46.578491, -16.185275 46.368945, -16.274714 46.159336, -16.36356 45.949665, -16.451854 45.739937, -16.539563 45.530148, -16.626695 45.3203, -16.713291 45.110395, -16.799343 44.900433, -16.884842 44.690414, -16.969802 44.480338, -17.054266 44.270209, -17.1382 44.060025, -17.221612 43.849785, -17.304534 43.639494, -17.386968 43.42915, -17.468899 43.218754, -17.550338 43.008305, -17.631332 42.797808, -17.711844 42.58726, -17.791881 42.376661, -17.871471 42.166014, -17.95062 41.955319, -18.029313 41.744575, -18.107556 41.533783, -18.185396 41.322946, -18.262798 41.112062, -18.339768 40.901131, -18.416329 40.690156, -18.492492 40.479136, -18.568239 40.268071, -18.643575 40.056962, -18.718542 39.845811, -18.793113 39.634617, -18.86729 39.423379, -18.941091 39.2121, -19.014532 39.00078, -19.087593 38.789418, -19.16028 38.578015, -19.232627 38.366574, -19.304616 38.155092, -19.376244 37.94357, -19.447526 37.732009, -19.518483 37.520411, -19.589092 37.308774, -19.659359 37.097099, -19.729313 36.885387, -19.798942 36.673638, -19.86824 36.461853, -19.93722 36.250031, -20.005905 36.038174, -20.074272 35.826281, -20.142325 35.614353, -20.21009 35.402391, -20.277559 35.190394, -20.344726 34.978363, -20.411599 34.766298, -20.478204 34.554201, -20.544517 34.342071, -20.610543 34.129907, -20.676302 33.917712, -20.741793 33.705485, -20.807006 33.493226, -20.871947 33.280936, -20.936645 33.068615, -21.001075 32.856263, -21.065242 32.643881, -21.129162 32.431469, -21.192838 32.219028, -21.256258 32.006557, -21.319428 31.794056, -21.382376 31.581527, -21.445078 31.36897, -21.507538 31.156384, -21.569769 30.94377, -21.631779 30.731129, -21.693554 30.51846, -21.755098 30.305764, -21.816437 30.093042, -21.877552 29.880293, -21.938444 29.667517, -21.999125 29.454716, -22.059603 29.241889, -22.119866 29.029036, -22.179917 28.816158, -22.239777 28.603255, -22.299433 28.390328, -22.358884 28.177376, -22.41814 27.9644, -22.477211 27.7514, -22.536084 27.538377, -22.594761 27.32533, -22.653262 27.112259, -22.711577 26.899166, -22.769704 26.686051, -22.827649 26.472912, -22.885426 26.259752, -22.94302 26.046569, -23.000436 25.833365, -23.057687 25.620139, -23.114769 25.406893, -23.171677 25.193625, -23.228418 24.980336, -23.285005 24.767026, -23.341424 24.553697, -23.397679 24.340347, -23.453781 24.126977, -23.509729 23.913587, -23.565518 23.700178, -23.621152 23.48675, -23.676644 23.273303, -23.731984 23.059836, -23.787172 22.846351, -23.842219 22.632848, -23.897125 22.419327, -23.951885 22.205788, -24.006501 21.99223, -24.060989 21.778656, -24.115337 21.565064, -24.169545 21.351454, -24.223623 21.137828, -24.277572 20.924185, -24.331388 20.710526, -24.385071 20.49685, -24.438636 20.283158, -24.492073 20.06945, -24.545382 19.855726, -24.598571 19.641987, -24.651643 19.428232, -24.704592 19.214462, -24.757421 19.000678, -24.81014 18.786878, -24.862742 18.573064, -24.915228 18.359235, -24.967603 18.145393, -25.019871 17.931536, -25.072028 17.717665, -25.124074 17.503781, -25.176018 17.289884, -25.227858 17.075973, -25.279591 16.862049, -25.331222 16.648112, -25.382755 16.434162, -25.434188 16.2202, -25.48552 16.006226, -25.536758 15.792239, -25.5879 15.578241, -25.638947 15.36423, -25.689899 15.150208, -25.740764 14.936175, -25.791536 14.72213, -25.842218 14.508074, -25.892813 14.294008, -25.943322 14.07993, -25.993744 13.865842, -26.044081 13.651744, -26.094338 13.437635, -26.144511 13.223517, -26.194602 13.009388, -26.244615 12.79525, -26.29455 12.581103, -26.344407 12.366946, -26.394186 12.15278, -26.443893 11.938605, -26.493525 11.724421, -26.543084 11.510228, -26.592571 11.296027, -26.641988 11.081818, -26.691335 10.867601, -26.740614 10.653375, -29.313131 11.22025, -29.265678 11.43462, -29.218189 11.648984, -29.170663 11.863344, -29.123112 12.077699, -29.075534 12.292051, -29.027915 12.506396, -28.980256 12.720736, -28.93258 12.935072, -28.88486 13.149402, -28.837097 13.363726, -28.7893 13.578045, -28.741471 13.792359, -28.693594 14.006666, -28.645669 14.220966, -28.597719 14.435261, -28.549721 14.649549, -28.50167 14.863831, -28.453578 15.078106, -28.405448 15.292374, -28.357263 15.506635, -28.309022 15.720889, -28.260748 15.935136, -28.212419 16.149375, -28.164031 16.363607, -28.115591 16.57783, -28.067109 16.792047, -28.018564 17.006255, -27.969955 17.220454, -27.921303 17.434646, -27.872592 17.64883, -27.823812 17.863004, -27.77497 18.077169, -27.726082 18.291326, -27.677123 18.505474, -27.62809 18.719612, -27.579005 18.933742, -27.529855 19.147862, -27.480628 19.361972, -27.431328 19.576071, -27.381976 19.790162, -27.332544 20.004242, -27.28303 20.218312, -27.233454 20.432372, -27.183806 20.646421, -27.134072 20.860459, -27.084254 21.074486, -27.034379 21.288503, -26.984414 21.502508, -26.934357 21.716502, -26.884227 21.930484, -26.83402 22.144455, -26.783716 22.358414, -26.733315 22.572361, -26.682853 22.786297, -26.632291 23.00022, -26.581626 23.21413, -26.530877 23.428028, -26.480043 23.641914, -26.429103 23.855786, -26.378055 24.069645, -26.326935 24.283492, -26.275706 24.497325, -26.224365 24.711144, -26.172925 24.92495, -26.121395 25.138743, -26.069747 25.352521, -26.017979 25.566285, -25.966127 25.780035, -25.914158 25.993771, -25.862066 26.207491, -25.809861 26.421197, -25.757557 26.634889, -25.705124 26.848566, -25.65256 27.062226, -25.599897 27.275872, -25.547109 27.489503, -25.494185 27.703117, -25.441133 27.916715, -25.387975 28.130298, -25.334674 28.343864, -25.281229 28.557413, -25.227671 28.770947, -25.173978 28.984464, -25.120136 29.197964, -25.066149 29.411446, -25.012047 29.624912, -24.957789 29.83836, -24.903373 30.05179, -24.848827 30.265203, -24.794137 30.478598, -24.739282 30.691975, -24.684265 30.905333, -24.629123 31.118674, -24.573811 31.331995, -24.518325 31.545297, -24.462691 31.758581, -24.406902 31.971845, -24.350933 32.18509, -24.294781 32.398315, -24.238495 32.611521, -24.182022 32.824707, -24.125359 33.037872, -24.068528 33.251017, -24.01153 33.464143, -23.954334 33.677247, -23.896937 33.890329, -23.839389 34.103392, -23.781639 34.316433, -23.72368 34.529451, -23.665532 34.742449, -23.607203 34.955425, -23.548658 35.168378, -23.489893 35.381308, -23.430956 35.594218, -23.3718 35.807104, -23.312416 36.019966, -23.252819 36.232806, -23.193027 36.445623, -23.132998 36.658416, -23.072727 36.871183, -23.01226 37.083929, -22.951558 37.29665, -22.890606 37.509345, -22.829415 37.722016, -22.768012 37.934663, -22.706349 38.147284, -22.644421 38.359878, -22.58227 38.572449, -22.519866 38.784993, -22.457186 38.99751, -22.394239 39.21, -22.331062 39.422466, -22.267599 39.634903, -22.203845 39.847312, -22.139839 40.059695, -22.075558 40.272051, -22.010975 40.484377, -21.946093 40.696675, -21.88096 40.908946, -21.815511 41.121187, -21.749744 41.333398, -21.683692 41.545581, -21.617341 41.757734, -21.550657 41.969857, -21.483638 42.181947, -21.416345 42.394011, -21.348705 42.606042, -21.280713 42.81804, -21.2124 43.030008, -21.143762 43.241945, -21.074757 43.453848, -21.005379 43.665718, -20.935694 43.877557, -20.865631 44.089363, -20.795178 44.301133, -20.724363 44.51287, -20.653193 44.724574, -20.581617 44.936242, -20.50963 45.147874, -20.437293 45.359473, -20.364543 45.571036, -20.291363 45.782561, -20.217774 45.994049, -20.143795 46.205503, -20.069368 46.416917, -19.994484 46.628292, -19.919204 46.839632, -19.84347 47.050933, -19.76726 47.262192, -19.690589 47.473412, -19.613488 47.684595, -19.535888 47.895736, -19.457783 48.106833, -19.379226 48.317892, -19.300171 48.528909, -19.220587 48.739882, -19.140481 48.950811, -19.0599 49.1617, -18.978764 49.372543, -18.897065 49.58334, -18.814852 49.794094, -18.732089 50.004803, -18.648736 50.215463, -14.766859 49.505215))"
              }],
             "style": {
                 "stroke_color": "red",
                 "fill_color": "rgba(255,0,0,0.3)",
             }
             },
             {"id": str(corrected_events[3].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[3].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16122</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[3].event_uuid) + "'><span class='bold-red'>MISSING</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-24T12:29:00.911137</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-24T12:29:00.911137</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                          "<tr><td>Playback type</td><td>SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF_2.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                  "value": "POLYGON ((-26.890228 10.001146, -29.457458 10.567606, -29.457458 10.567606, -26.890228 10.001146))"
              }],
              "style": {
                  "stroke_color": "red",
                  "fill_color": "rgba(255,0,0,0.3)",
              }
            }
        ]

        returned_acquisition_geometries_missing = self.driver.execute_script('return acquisition_geometries_missing;')
        returned_acquisition_geometries_missing.sort(key=lambda x:x["id"])

        acquisition_geometries_received = [
            {"id": str(playback_completeness_channel_1[0].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td>MPS_</td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.728601</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.719834</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
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
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td>MPS_</td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.760977</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.753003</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
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
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td>MPS_</td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:20.858708</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:26.355940</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.092</td></tr>" +
                          "<tr><td>Playback type</td><td>SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
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

        returned_acquisition_geometries_received = self.driver.execute_script('return acquisition_geometries_received;')
        returned_acquisition_geometries_received.sort(key=lambda x:x["id"])
        assert acquisition_geometries_received == returned_acquisition_geometries_received

        # Station Reports table

        station_reports_table = self.driver.find_element_by_id("station-acquisition-reports-table")

        satellite = station_reports_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        orbit = station_reports_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert orbit.text == "16122"

        station = station_reports_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "MPS_"

        antenna_id = station_reports_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert antenna_id.text == "MSP21"

        status = station_reports_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert status.text == "OK"

        comments = station_reports_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert comments.text == ""

        start = station_reports_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert start.text == "2018-07-24 12:17:23"

        stop = station_reports_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert stop.text == "2018-07-24 12:29:32"

        source = station_reports_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert source.text == "S2A_STNACQ.EOF"

        uuid = station_reports_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert re.match("........-....-....-....-............", uuid.text)

    def test_acquisition_only_nppf_orbpre_and_rep_pass_with_gaps(self):
        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_REP_PASS_CONTAINING_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

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

        satellite = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[1]")

        assert satellite.text == "S2A"

        orbit = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[2]")

        assert orbit.text == "16078"

        station = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[3]")

        assert station.text == ""

        playback_type = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[4]")

        assert playback_type.text == "NOMINAL"

        playback_status = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[5]")

        assert playback_status.text == "GAPS"
        
        playback_isp_completeness = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[6]")

        assert playback_isp_completeness.text == "INCOMPLETE"

        playback_missing_packets = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[7]")

        assert playback_missing_packets.text == "400.0"

        link_session = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[8]")

        assert link_session.text == "REP_PASS_2_2018-07-21T10:35:27"

        start = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[9]")

        assert start.text == "2018-07-21T10:35:32.524661"

        stop = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[10]")

        assert stop.text == "2018-07-21T10:37:08.530863"

        duration_s = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[11]")

        assert duration_s.text == "96.006"

        duration_m = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[12]")

        assert duration_m.text == "1.6"

        parameters = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[13]")

        assert parameters.text == "MEM_FREE=1\nSCN_DUP=0\nSCN_RWD=1"

        station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[14]")

        assert station_schedule.text == "MISSING"

        dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[15]")

        assert station_schedule.text == "MISSING"

        delta_start_acq = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[16]")

        assert delta_start_acq.text == "-1.204"

        delta_stop_acq = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[17]")

        assert delta_stop_acq.text == "-6.189"

        delta_start_station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[18]")

        assert delta_start_station_schedule.text == "N/A"

        delta_stop_station_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[19]")

        assert delta_stop_station_schedule.text == "N/A"

        delta_start_dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[20]")

        assert delta_start_dfep_schedule.text == "N/A"

        delta_stop_dfep_schedule = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[21]")

        assert delta_stop_dfep_schedule.text == "N/A"

        plan_file = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[22]")

        assert plan_file.text == "S2A_NPPF.EOF"

        uuid = acquisition_details_table.find_element_by_xpath("tbody/tr[last()]/td[24]")

        assert re.match("........-....-....-....-............", uuid.text)


        original_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"=="})

        original_events.sort(key=lambda x:x.start)

        corrected_events = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_CORRECTION", "op":"=="})

        corrected_events.sort(key=lambda x:x.start)

        playback_completeness_channel_1 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_1", "op":"=="})

        playback_completeness_channel_1.sort(key=lambda x:x.start)

        playback_completeness_channel_2 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2", "op":"=="})

        playback_completeness_channel_2.sort(key=lambda x:x.start)

        # Timeline
        acquisition_timeline_received = [
            {"id": str(playback_completeness_channel_2[0].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:35:33.760977",
             "stop": "2018-07-21T10:37:14.753003",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.760977</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.753003</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-green"
             },
            {"id": str(playback_completeness_channel_2[1].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:37:20.858708",
             "stop": "2018-07-21T10:37:26.355940",
             "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:20.858708</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:26.355940</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.092</td></tr>" +
                          "<tr><td>Playback type</td><td>SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "className": "fill-border-green"
            }
        ]

        returned_received_playbacks_timeline = self.driver.execute_script('return received_playbacks_timeline;')
        returned_received_playbacks_timeline.sort(key=lambda x:x["start"])
        assert acquisition_timeline_received == returned_received_playbacks_timeline

        # Timeline
        acquisition_timeline_incomplete = [
            {"id": str(playback_completeness_channel_1[0].event_uuid),
             "group": "S2A",
             "timeline": "",
             "start": "2018-07-21T10:35:33.728601",
             "stop": "2018-07-21T10:37:14.719834",
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-orange'>INCOMPLETE</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.728601</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.719834</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
            "className": "fill-border-orange"
             }
        ]

        returned_incomplete_playbacks_timeline = self.driver.execute_script('return incomplete_playbacks_timeline;')
        returned_incomplete_playbacks_timeline.sort(key=lambda x:x["start"])
        assert acquisition_timeline_incomplete == returned_incomplete_playbacks_timeline
        
        # Map
        acquisition_geometries_received = [
            {"id": str(playback_completeness_channel_2[0].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.760977</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.753003</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
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
                          "<tr><td>UUID</td><td>" + str(original_events[1].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[1].event_uuid) + "'><span class='bold-green'>RECEIVED</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:37:20.858708</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:26.355940</td></tr>" +
                          "<tr><td>Duration(m)</td><td>0.092</td></tr>" +
                          "<tr><td>Playback type</td><td>SAD</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
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

        returned_acquisition_geometries_received = self.driver.execute_script('return acquisition_geometries_received;')
        returned_acquisition_geometries_received.sort(key=lambda x:x["id"])
        assert acquisition_geometries_received == returned_acquisition_geometries_received

        # Map
        acquisition_geometries_incomplete = [
            {"id": str(playback_completeness_channel_1[0].event_uuid),
              "tooltip": "<table border='1'>" +
                          "<tr><td>UUID</td><td>" + str(original_events[0].event_uuid) + "</td></tr>" +
                          "<tr><td>Satellite</td><td>S2A</td></tr>" +
                          "<tr><td>Orbit</td><td>16078</td></tr>" +
                          "<tr><td>Station</td><td></td></tr>" +
                          "<tr><td>Status</td><td><a href='/views/specific-acquisition/" + str(corrected_events[0].event_uuid) + "'><span class='bold-orange'>INCOMPLETE</span></a></td></tr>" +
                          "<tr><td>Start</td><td>2018-07-21T10:35:33.728601</td></tr>" +
                          "<tr><td>Stop</td><td>2018-07-21T10:37:14.719834</td></tr>" +
                          "<tr><td>Duration(m)</td><td>1.683</td></tr>" +
                          "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                          "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                          "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                          '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(original_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                          "</table>",
              "geometries":[{
                     "name": "footprint",
                     "value": "POLYGON ((3.070036 19.546021, 3.015189 19.324835, 2.960462 19.103632, 2.905864 18.882414, 2.851391 18.66118, 2.79704 18.439931, 2.742805 18.218667, 2.688691 17.997387, 2.634696 17.776092, 2.580816 17.554783, 2.527047 17.33346, 2.473393 17.112122, 2.419851 16.89077, 2.366418 16.669405, 2.31309 16.448025, 2.259871 16.226633, 2.206759 16.005227, 2.153748 15.783808, 2.100839 15.562377, 2.048032 15.340932, 1.995326 15.119476, 1.942715 14.898007, 1.890201 14.676526, 1.837783 14.455034, 1.785461 14.233529, 1.733228 14.012014, 1.681087 13.790487, 1.629037 13.568949, -0.972041 14.138141, -0.92244 14.35988, -0.872787 14.581612, -0.823084 14.803337, -0.773348 15.025056, -0.723556 15.246768, -0.673708 15.468471, -0.623807 15.690167, -0.573867 15.911855, -0.523867 16.133536, -0.473804 16.355208, -0.423688 16.576872, -0.373525 16.798528, -0.323296 17.020175, -0.273 17.241813, -0.222649 17.463442, -0.172242 17.685063, -0.121765 17.906674, -0.071215 18.128275, -0.02061 18.349867, 0.03006 18.57145, 0.080806 18.793023, 0.13163 19.014585, 0.182511 19.236137, 0.233464 19.457679, 0.2845 19.67921, 0.335619 19.90073, 0.386797 20.122241, 3.070036 19.546021))"
              }],
             "style": {
                 "stroke_color": "orange",
                 "fill_color": "rgba(255,140,0,0.3)",
             }
             }
        ]

        returned_acquisition_geometries_incomplete = self.driver.execute_script('return acquisition_geometries_incomplete;')
        returned_acquisition_geometries_incomplete.sort(key=lambda x:x["id"])
        assert acquisition_geometries_incomplete == returned_acquisition_geometries_incomplete

        station_reports_no_data = wait.until(EC.visibility_of_element_located((By.ID,"station-reports-no-reports")))

        assert station_reports_no_data

    def test_acquisition_mmfu_half_swath_missing(self):

        filename = "S2B_OPER_MPL__NPPF__20210107T120000_20210125T150000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_MPL_ORBPRE_20210112T030110_20210122T030110_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_MPL_SPSGS__PDMC_20210111T090001_V20210112T090000_20210118T090000.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_REP_PASS_E_VGS2_20210112T182418_V20210112T181713_20210112T182415.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_REP_PASS_E_VGS2_20210112T182433_V20210112T181714_20210112T182430.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        wait = WebDriverWait(self.driver,5);
        
        self.driver.get("http://localhost:5000/views/acquisition")

        functions.query(self.driver, wait, "S2_", start = "2014-07-20T00:00:14", stop = "2021-07-21T23:55:14", table_details = True, map = True, station_reports = True)

        #Acquisitions table

        table = self.driver.find_element_by_id("acquisition-details-table")

        rows_half_swath_mmfu_anomaly = table.find_elements_by_xpath("tbody/tr/td/a[contains(text(),'(possible MMFU half swath anomaly)')]")
        
        assert len(rows_half_swath_mmfu_anomaly) == 1

        table = self.driver.find_element_by_id("acquisition-missing-table")

        rows_half_swath_mmfu_anomaly = table.find_elements_by_xpath("tbody/tr/td/a[contains(text(),'(possible MMFU half swath anomaly)')]")

        assert len(rows_half_swath_mmfu_anomaly) == 1

