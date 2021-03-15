"""
Automated tests for the processing view

Written by DEIMOS Space S.L. (jubv)

module vboa
"""
import os
import sys
import unittest
import time
import subprocess
import datetime
import s2vboa.tests.processing.aux_functions as functions
import vboa.tests.functions as functions_vboa
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


class TestProcessingView(unittest.TestCase):
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

    def test_processing_no_data(self):

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/processing")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "16077", stop_orbit = "16079", map = True, timeline = True)

        # Check header generated
        header_no_data = wait.until(EC.visibility_of_element_located((By.ID,"header-no-data")))

        assert header_no_data

        table_details_no_data = wait.until(EC.visibility_of_element_located((By.ID,"no-processing-data")))

        assert table_details_no_data
    
    def test_processing_only_nppf_and_orbpre(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0
        
        wait = WebDriverWait(self.driver,5)

        filename = "S2A_REP_PASS_NO_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        self.driver.get("http://localhost:5000/views/processing")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "16077", stop_orbit = "16079", map = True, timeline = True)

        # Check summary pies
        # L0
        processing_data_l0_pie_info = [0,1]

        returned_processing_data_l0_pie_info = self.driver.execute_script('return processing_data_l0;')
        assert processing_data_l0_pie_info == returned_processing_data_l0_pie_info

        # L1B
        processing_data_l1b_pie_info = [0,1]

        returned_processing_data_l1b_pie_info = self.driver.execute_script('return processing_data_l1b;')
        assert processing_data_l1b_pie_info == returned_processing_data_l1b_pie_info

        # L1C
        processing_data_l1c_pie_info = [0,1]

        returned_processing_data_l1c_pie_info = self.driver.execute_script('return processing_data_l1c;')
        assert processing_data_l1c_pie_info == returned_processing_data_l1c_pie_info
        
        # L2A
        processing_data_l2a_pie_info = [0,1]

        returned_processing_data_l2a_pie_info = self.driver.execute_script('return processing_data_l2a;')
        assert processing_data_l2a_pie_info == returned_processing_data_l2a_pie_info
        
        # Check summary expected playbacks
        summary_expected_playbacks = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-playbacks")))

        assert summary_expected_playbacks

        assert summary_expected_playbacks.text == "1"

        # Check summary expected datastrips
        summary_expected_datastrips = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-datastrips")))

        assert summary_expected_datastrips

        assert summary_expected_datastrips.text == "1"

        # Check summary missing processing L0
        summary_missing_processing_l0 = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l0")))

        assert summary_missing_processing_l0

        assert summary_missing_processing_l0.text == "1"

        # Check summary missing processing L1B
        summary_missing_processing_l1b = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1b")))

        assert summary_missing_processing_l1b

        assert summary_missing_processing_l1b.text == "1"

        # Check summary missing processing L1C
        summary_missing_processing_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1c")))

        assert summary_missing_processing_l1c

        assert summary_missing_processing_l1c.text == "1"

        # Check summary missing processing L2A
        summary_missing_processing_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l2a")))

        assert summary_missing_processing_l2a

        assert summary_missing_processing_l2a.text == "1"

        # Check summary processing table
        summary_table = self.driver.find_element_by_id("summary-processing-table")

        # Row 1
        level = summary_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L0"

        expected = summary_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert expected.text == "1"

        missing = summary_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert missing.text == "1"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert performance.text == "0.0"

        # Row 2
        level = summary_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1B"

        expected = summary_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert expected.text == "1"

        missing = summary_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert missing.text == "1"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert performance.text == "0.0"

        # Row 3
        level = summary_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L1C"

        expected = summary_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert expected.text == "1"

        missing = summary_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert missing.text == "1"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert performance.text == "0.0"

        # Row 4
        level = summary_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert level.text == "L2A"

        expected = summary_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert expected.text == "1"

        missing = summary_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert missing.text == "1"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert performance.text == "0.0"

        # Check whether the maps are displayed
        map_section = self.driver.find_element_by_id("processing-on-map-section")

        condition = map_section.is_displayed()

        assert condition is True
        
        # Check map complete segments tooltip
        planned_playback_correction = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_CORRECTION", "op":"=="},
                                                                start_filters =[{"date": "2018-07-21T10:35:32.524661", "op":"=="}],
                                                                stop_filters = [{"date": "2018-07-21T10:37:08.530863", "op": "=="}])
        sad_data = self.query_eboa.get_events(gauge_names ={"filter": "SAD_DATA", "op":"=="},
                                            start_filters =[{"date": "2018-07-20T22:00:21.024658", "op":"=="}],
                                            stop_filters = [{"date": "2018-07-21T10:37:11.024915", "op": "=="}])
        isp_validity = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY", "op":"=="},
                                                start_filters =[{"date": "2018-07-21T08:52:29.993268", "op":"=="}],
                                                stop_filters = [{"date": "2018-07-21T08:54:18.226646", "op": "=="}])
        planned_playback = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"=="},
                                                    start_filters =[{"date": "2018-07-21T10:35:27.430000", "op":"=="}],
                                                    stop_filters = [{"date": "2018-07-21T10:37:03.431000", "op": "=="}])
        # L0
        isp_validity_processing_completeness_l0 = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0_CHANNEL_2", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:35.993268", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:12.226646", "op": "=="}])
        
        map_l0_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l0[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l0[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.604</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l0 = self.driver.execute_script('return processing_geometries_missing_l0;') 
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l0, map_l0_missing_tooltip_info)

        # L1B
        isp_validity_processing_completeness_l1b = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1B_CHANNEL_2", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:35.993268", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:12.226646", "op": "=="}])

        map_l1b_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l1b[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1b[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.604</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l0 = self.driver.execute_script('return processing_geometries_missing_l1b;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l0, map_l1b_missing_tooltip_info)

        # L1C
        isp_validity_processing_completeness_l1c = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1C_CHANNEL_2", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:35.993268", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:12.226646", "op": "=="}])
        
        map_l1c_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l1c[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1c[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.604</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            }, 
        ]

        returned_processing_geometries_missing_l1c = self.driver.execute_script('return processing_geometries_missing_l1c;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l1c, map_l1c_missing_tooltip_info)

        # L2A
        isp_validity_processing_completeness_l2a = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L2A_CHANNEL_2", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:35.993268", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:12.226646", "op": "=="}])
        
        map_l2a_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l2a[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l2a[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.604</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            }, 
        ]

        returned_processing_geometries_missing_l2a = self.driver.execute_script('return processing_geometries_missing_l2a;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l2a, map_l2a_missing_tooltip_info)

        # Check whether the timeline is displayed
        timeline_section = self.driver.find_element_by_id("processing-timeline-section")

        condition = timeline_section.is_displayed()
        assert condition is True

        # Check timeline segments tooltip
        # Missing
        missing_timeline_tooltip_info = [
            {
                "className": "fill-border-red",
                "group": "S2A;MPS_",
                "id": str(isp_validity_processing_completeness_l0[0].event_uuid),
                "start": "2018-07-21T08:52:35.993268",
                "stop": "2018-07-21T08:54:12.226646",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.604</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2A;MPS_",
                "id": str(isp_validity_processing_completeness_l1b[0].event_uuid),
                "start": "2018-07-21T08:52:35.993268",
                "stop": "2018-07-21T08:54:12.226646",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.604</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2A;MPS_",
                "id": str(isp_validity_processing_completeness_l1c[0].event_uuid),
                "start": "2018-07-21T08:52:35.993268",
                "stop": "2018-07-21T08:54:12.226646",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.604</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            },     
            {
                "className": "fill-border-red",
                "group": "S2A;MPS_",
                "id": str(isp_validity_processing_completeness_l2a[0].event_uuid),
                "start": "2018-07-21T08:52:35.993268",
                "stop": "2018-07-21T08:54:12.226646",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.604</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            },
        ]

        returned_missing_processing_timeline = self.driver.execute_script('return missing_processing_timeline;')
        functions_vboa.verify_js_var(returned_missing_processing_timeline, missing_timeline_tooltip_info)
        
        # Complete
        complete_timeline_tooltip_info = []

        returned_complete_processing_timeline = self.driver.execute_script('return complete_processing_timeline;')
        assert complete_timeline_tooltip_info == returned_complete_processing_timeline

        # Incomplete
        incomplete_timeline_tooltip_info = []

        returned_incomplete_processing_timeline = self.driver.execute_script('return incomplete_processing_timeline;')
        assert incomplete_timeline_tooltip_info == returned_incomplete_processing_timeline

        # Check processing missing table
        missing_table = self.driver.find_element_by_id("processing-missing-table")

        # Row 1
        satellite = missing_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = missing_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "MPS_"

        level = missing_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = missing_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"
        
        duration = missing_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 2
        satellite = missing_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = missing_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "MPS_"

        level = missing_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = missing_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = missing_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 3
        satellite = missing_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = missing_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "MPS_"

        level = missing_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = missing_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"
        
        duration = missing_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 4
        satellite = missing_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = missing_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "MPS_"

        level = missing_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = missing_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = missing_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"
        
        # Check processing completeness table
        completeness_table = self.driver.find_element_by_id("processing-completeness-table")

        # Row 1
        satellite = completeness_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "MPS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = completeness_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = completeness_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 2
        satellite = completeness_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "MPS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = completeness_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = completeness_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 3
        satellite = completeness_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "MPS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = completeness_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = completeness_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 4
        satellite = completeness_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "MPS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = completeness_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = completeness_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Datastrip by UUID missing table
        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/specific-processing/" + str(planned_playback[0].event_uuid))

        missing_datastrip_table = self.driver.find_element_by_id("processing-missing-table")

         # Row 1
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "MPS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 2
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "MPS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 3
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "MPS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 4
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "MPS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"
        
        # Datastrip by UUID completeness table
        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/specific-processing/" + str(planned_playback[0].event_uuid))

        completeness_datastrip_table = self.driver.find_element_by_id("processing-completeness-table")

         # Row 1
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "MPS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 2
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "MPS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 3
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "MPS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 4
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "MPS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2018-07-21T08:52:35.993268"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2018-07-21T08:54:12.226646"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "1.604"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

    
    def test_processing_dpc_L0_L1B_L1C_L2A_with_plan_and_rep_pass(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_REP_PASS_NO_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_OPDPC_L0U_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_OPDPC_L0_L1B.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_OPDPC_L1B_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_OPDPC_L1C_L2A.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0
        
        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/processing")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "16077", stop_orbit = "16079", map = True, timeline = True)

        # Check summary pies
        # L0
        processing_data_l0_pie_info = [1,0]

        returned_processing_data_l0_pie_info = self.driver.execute_script('return processing_data_l0;')
        assert processing_data_l0_pie_info == returned_processing_data_l0_pie_info

        # L1B
        processing_data_l1b_pie_info = [1,0]

        returned_processing_data_l1b_pie_info = self.driver.execute_script('return processing_data_l1b;')
        assert processing_data_l1b_pie_info == returned_processing_data_l1b_pie_info

        # L1C
        processing_data_l1c_pie_info = [1,0]

        returned_processing_data_l1c_pie_info = self.driver.execute_script('return processing_data_l1c;')
        assert processing_data_l1c_pie_info == returned_processing_data_l1c_pie_info
        
        # L2A
        processing_data_l2a_pie_info = [1,0]

        returned_processing_data_l2a_pie_info = self.driver.execute_script('return processing_data_l2a;')
        assert processing_data_l2a_pie_info == returned_processing_data_l2a_pie_info
        
        # Check summary expected playbacks
        summary_expected_playbacks = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-playbacks")))

        assert summary_expected_playbacks

        assert summary_expected_playbacks.text == "1"

        # Check summary expected datastrips
        summary_expected_datastrips = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-datastrips")))

        assert summary_expected_datastrips

        assert summary_expected_datastrips.text == "1"

        # Check summary processing table
        summary_table = self.driver.find_element_by_id("summary-processing-table")

        # Row 1
        level = summary_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L0"

        expected = summary_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert expected.text == "1"

        missing = summary_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert missing.text == "0"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert performance.text == "100.0"

        # Row 2
        level = summary_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1B"

        expected = summary_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert expected.text == "1"

        missing = summary_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert missing.text == "0"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert performance.text == "100.0"

        # Row 3
        level = summary_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L1C"

        expected = summary_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert expected.text == "1"

        missing = summary_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert missing.text == "0"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert performance.text == "100.0"

        # Row 4
        level = summary_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert level.text == "L2A"

        expected = summary_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert expected.text == "1"

        missing = summary_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert missing.text == "0"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert performance.text == "100.0"

        # Check whether the maps are displayed
        map_section = self.driver.find_element_by_id("processing-on-map-section")

        condition = map_section.is_displayed()

        assert condition is True
        
        # Check map complete segments tooltip
        planned_playback_correction = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_CORRECTION", "op":"=="},
                                                                start_filters =[{"date": "2018-07-21T10:35:32.524661", "op":"=="}],
                                                                stop_filters = [{"date": "2018-07-21T10:37:08.530863", "op": "=="}])
        sad_data = self.query_eboa.get_events(gauge_names ={"filter": "SAD_DATA", "op":"=="},
                                            start_filters =[{"date": "2018-07-20T22:00:21.024658", "op":"=="}],
                                            stop_filters = [{"date": "2018-07-21T10:37:11.024915", "op": "=="}])
        isp_validity = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY", "op":"=="},
                                                start_filters =[{"date": "2018-07-21T08:52:29.993268", "op":"=="}],
                                                stop_filters = [{"date": "2018-07-21T08:54:18.226646", "op": "=="}])
        planned_playback = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"=="},
                                                    start_filters =[{"date": "2018-07-21T10:35:27.430000", "op":"=="}],
                                                    stop_filters = [{"date": "2018-07-21T10:37:03.431000", "op": "=="}])
        # L0
        isp_validity_processing_completeness_l0 = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0_CHANNEL_2", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:29", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])
        processing_validity_l0 = self.query_eboa.get_events(gauge_names ={"filter": "PROCESSING_VALIDITY", "op":"=="},
                                                            start_filters =[{"date": "2018-07-21T08:52:29", "op":"=="}],
                                                            stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])
        
        map_l0_complete_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l0[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l0[0].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "'>S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + processing_validity_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + processing_validity_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.833</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_complete_l0 = self.driver.execute_script('return processing_geometries_complete_l0;')
        functions_vboa.verify_js_var(returned_processing_geometries_complete_l0, map_l0_complete_tooltip_info)

        # L1B
        isp_validity_processing_completeness_l1b = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1B_CHANNEL_2", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:31", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])
        processing_validity_l1b = self.query_eboa.get_events(gauge_names ={"filter": "PROCESSING_VALIDITY", "op":"=="},
                                                            start_filters =[{"date": "2018-07-21T08:52:31", "op":"=="}],
                                                            stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])
        map_l1b_complete_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l1b[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1b[0].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "'>S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + processing_validity_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + processing_validity_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.717</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_complete_l1b = self.driver.execute_script('return processing_geometries_complete_l1b;')
        functions_vboa.verify_js_var(returned_processing_geometries_complete_l1b, map_l1b_complete_tooltip_info)

        # L1C
        isp_validity_processing_completeness_l1c = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1C_CHANNEL_2", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:31", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])
        processing_validity_l1c = self.query_eboa.get_events(gauge_names ={"filter": "PROCESSING_VALIDITY", "op":"=="},
                                                            start_filters =[{"date": "2018-07-21T08:52:31", "op":"=="}],
                                                            stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])
        
        map_l1c_complete_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l1c[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1c[0].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "'>S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + processing_validity_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + processing_validity_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.717</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_complete_l1c = self.driver.execute_script('return processing_geometries_complete_l1c;')
        functions_vboa.verify_js_var(returned_processing_geometries_complete_l1c, map_l1c_complete_tooltip_info)

        # L2A
        isp_validity_processing_completeness_l2a = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L2A_CHANNEL_2", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:31", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])
        processing_validity_l2a = self.query_eboa.get_events(gauge_names ={"filter": "PROCESSING_VALIDITY", "op":"=="},
                                                            start_filters =[{"date": "2018-07-21T08:52:31", "op":"=="}],
                                                            stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])
        
        map_l2a_complete_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l2a[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l2a[0].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "'>S2A_OPER_MSI_L2A_DS_MPS__20180721T110122_S20180721T085229_N02.08</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + processing_validity_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + processing_validity_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.717</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            }, 
        ]

        returned_processing_geometries_complete_l2a = self.driver.execute_script('return processing_geometries_complete_l2a;')
        functions_vboa.verify_js_var(returned_processing_geometries_complete_l2a, map_l2a_complete_tooltip_info)

        # Check whether the timeline is displayed
        timeline_section = self.driver.find_element_by_id("processing-timeline-section")

        condition = timeline_section.is_displayed()
        assert condition is True

        # Check timeline segments tooltip
        # Missing
        missing_timeline_tooltip_info = []

        returned_missing_processing_timeline = self.driver.execute_script('return missing_processing_timeline;')
        assert missing_timeline_tooltip_info == returned_missing_processing_timeline
        # Complete
        complete_timeline_tooltip_info = [
            {
                "className": "fill-border-green",
                "group": "S2A;MPS_",
                "id": str(isp_validity_processing_completeness_l0[0].event_uuid),
                "start": "2018-07-21T08:52:29",
                "stop": "2018-07-21T08:54:19",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "'>S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + processing_validity_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + processing_validity_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.833</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-green",
                "group": "S2A;MPS_",
                "id": str(isp_validity_processing_completeness_l1b[0].event_uuid),
                "start": "2018-07-21T08:52:31",
                "stop": "2018-07-21T08:54:14",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "'>S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + processing_validity_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + processing_validity_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.717</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-green",
                "group": "S2A;MPS_",
                "id": str(isp_validity_processing_completeness_l1c[0].event_uuid),
                "start": "2018-07-21T08:52:31",
                "stop": "2018-07-21T08:54:14",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "'>S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + processing_validity_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + processing_validity_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.717</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            },     
            {
                "className": "fill-border-green",
                "group": "S2A;MPS_",
                "id": str(isp_validity_processing_completeness_l2a[0].event_uuid),
                "start": "2018-07-21T08:52:31",
                "stop": "2018-07-21T08:54:14",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>16078.0</a></td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "'>S2A_OPER_MSI_L2A_DS_MPS__20180721T110122_S20180721T085229_N02.08</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + processing_validity_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + processing_validity_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.717</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915</a></td></tr>" +
                "</table>"
            },
        ]

        returned_complete_processing_timeline = self.driver.execute_script('return complete_processing_timeline;')
        functions_vboa.verify_js_var(returned_complete_processing_timeline, complete_timeline_tooltip_info)

        # Incomplete
        incomplete_timeline_tooltip_info = []

        returned_incomplete_processing_timeline = self.driver.execute_script('return incomplete_processing_timeline;')
        assert incomplete_timeline_tooltip_info == returned_incomplete_processing_timeline

        # Check processing completeness table
        completeness_table = self.driver.find_element_by_id("processing-completeness-table")

        # Row 1
        satellite = completeness_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "MPS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2018-07-21T08:52:29"

        stop = completeness_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2018-07-21T08:54:19"

        duration = completeness_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "1.833"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 2
        satellite = completeness_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "MPS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2018-07-21T08:52:31"

        stop = completeness_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2018-07-21T08:54:14"

        duration = completeness_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "1.717"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 3
        satellite = completeness_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "MPS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2018-07-21T08:52:31"

        stop = completeness_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2018-07-21T08:54:14"

        duration = completeness_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "1.717"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 4
        satellite = completeness_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "MPS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L2A_DS_MPS__20180721T110122_S20180721T085229_N02.08"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2018-07-21T08:52:31"

        stop = completeness_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2018-07-21T08:54:14"

        duration = completeness_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "1.717"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Datastrip by UUID completeness table
        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/specific-processing/" + str(planned_playback[0].event_uuid))

        completeness_datastrip_table = self.driver.find_element_by_id("processing-completeness-table")

        # Row 1
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "MPS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2018-07-21T08:52:29"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2018-07-21T08:54:19"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "1.833"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 2
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "MPS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2018-07-21T08:52:31"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2018-07-21T08:54:14"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "1.717"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 3
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "MPS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2018-07-21T08:52:31"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2018-07-21T08:54:14"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "1.717"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

        # Row 4
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "MPS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L2A_DS_MPS__20180721T110122_S20180721T085229_N02.08"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2018-07-21T08:52:31"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2018-07-21T08:54:14"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "1.717"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2018-07-20T22:00:21.024658_2018-07-21T10:37:11.024915"

    def test_processing_with_rep_pass_e_vgs(self):

        filename = "S2B_OPER_MPL__NPPF__20210218T120000_20210308T150000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_MPL_ORBPRE_20210221T030153_20210303T030153_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_MPL_SPSGS__PDMC_20210221T090000_V20210222T090000_20210228T090000.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_REP_PASS_E_VGS2_20210222T193404_V20210222T191105_20210222T191846.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_REP_PASS_E_VGS2_20210222T193412_V20210222T191106_20210222T191854.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/processing")

        functions.query(self.driver, wait, "S2B", start = "2021-02-18T12:00:00", stop = "2021-03-08T15:00:00", start_orbit = "20706", stop_orbit = "20720", map = True, timeline = True)

        # Check summary pies
        # L0
        processing_data_l0_pie_info = [0,3]

        returned_processing_data_l0_pie_info = self.driver.execute_script('return processing_data_l0;')
        assert processing_data_l0_pie_info == returned_processing_data_l0_pie_info

        # L1B
        processing_data_l1b_pie_info = [0,3]

        returned_processing_data_l1b_pie_info = self.driver.execute_script('return processing_data_l1b;')
        assert processing_data_l1b_pie_info == returned_processing_data_l1b_pie_info

        # L1C
        processing_data_l1c_pie_info = [0,3]

        returned_processing_data_l1c_pie_info = self.driver.execute_script('return processing_data_l1c;')
        assert processing_data_l1c_pie_info == returned_processing_data_l1c_pie_info
        
        # L2A
        processing_data_l2a_pie_info = [0,3]

        returned_processing_data_l2a_pie_info = self.driver.execute_script('return processing_data_l2a;')
        assert processing_data_l2a_pie_info == returned_processing_data_l2a_pie_info
        
        # Check summary expected playbacks
        summary_expected_playbacks = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-playbacks")))

        assert summary_expected_playbacks

        assert summary_expected_playbacks.text == "1"

        # Check summary expected datastrips
        summary_expected_datastrips = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-datastrips")))

        assert summary_expected_datastrips

        assert summary_expected_datastrips.text == "3"

        # Check summary expected missing processing L0
        summary_expected_missing_processing_l0 = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l0")))

        assert summary_expected_missing_processing_l0

        assert summary_expected_missing_processing_l0.text == "3"

        # Check summary expected missing processing L1B
        summary_expected_missing_processing_l1b = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1b")))

        assert summary_expected_missing_processing_l1b

        assert summary_expected_missing_processing_l1b.text == "3"

        # Check summary expected missing processing L1C
        summary_expected_missing_processing_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1c")))

        assert summary_expected_missing_processing_l1c

        assert summary_expected_missing_processing_l1c.text == "3"

        # Check summary expected missing processing L2A
        summary_expected_missing_processing_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l2a")))

        assert summary_expected_missing_processing_l2a

        assert summary_expected_missing_processing_l2a.text == "3"

        # Check summary processing table
        summary_table = self.driver.find_element_by_id("summary-processing-table")

        # Row 1
        level = summary_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L0"

        expected = summary_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert performance.text == "0.0"

        # Row 2
        level = summary_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1B"

        expected = summary_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert performance.text == "0.0"

        # Row 3
        level = summary_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L1C"

        expected = summary_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert performance.text == "0.0"

        # Row 4
        level = summary_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert level.text == "L2A"

        expected = summary_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert performance.text == "0.0"

        # Check whether the maps are displayed
        map_section = self.driver.find_element_by_id("processing-on-map-section")

        condition = map_section.is_displayed()

        assert condition is True
        
        # Check map complete segments tooltip
        planned_playback_correction = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_CORRECTION", "op":"=="},
                                                                start_filters =[{"date": "2021-02-22T19:11:03.543116", "op":"=="}],
                                                                stop_filters = [{"date": "2021-02-22T19:22:43.099034", "op": "=="}])
        sad_data = self.query_eboa.get_events(gauge_names ={"filter": "SAD_DATA", "op":"=="},
                                            start_filters =[{"date": "2021-02-22T05:54:39.024895", "op":"=="}],
                                            stop_filters = [{"date": "2021-02-22T19:22:49.024749", "op": "=="}])
        isp_validity = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY", "op":"=="},
                                                  value_filters = [{"name": {"op": "==", "filter": "channel"},
                                                                    "type": "double",
                                                                    "value": {"op": "==", "filter": "2"}}],
                                                  order_by = {"field": "start", "descending": False})
        planned_playback = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"=="},
                                                    start_filters =[{"date": "2021-02-22T19:11:01.731000", "op":"=="}],
                                                    stop_filters = [{"date": "2021-02-22T19:22:40.627000", "op": "=="}])
        # L0
        isp_validity_processing_completeness_l0 = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0_CHANNEL_2", "op":"=="},
                                                                             order_by = {"field": "start", "descending": False})
        
        map_l0_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l0[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l0[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l0[1].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l0[1].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l0[2].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l0[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l0 = self.driver.execute_script('return processing_geometries_missing_l0;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l0, map_l0_missing_tooltip_info)

        # L1B
        isp_validity_processing_completeness_l1b = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1B_CHANNEL_2", "op":"=="},
                                                                             order_by = {"field": "start", "descending": False})
        
        map_l1b_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l1b[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1b[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l1b[1].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1b[1].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l1b[2].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1b[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l1b = self.driver.execute_script('return processing_geometries_missing_l1b;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l1b, map_l1b_missing_tooltip_info)

        # L1C
        isp_validity_processing_completeness_l1c = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1C_CHANNEL_2", "op":"=="},
                                                                             order_by = {"field": "start", "descending": False})
        
        map_l1c_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l1c[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1c[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l1c[1].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1c[1].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l1c[2].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1c[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l1c = self.driver.execute_script('return processing_geometries_missing_l1c;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l1c, map_l1c_missing_tooltip_info)

        # L2A
        isp_validity_processing_completeness_l2a = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L2A_CHANNEL_2", "op":"=="},
                                                                             order_by = {"field": "start", "descending": False})
        
        map_l2a_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l2a[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l2a[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l2a[1].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l2a[1].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l2a[2].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l2a[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l2a = self.driver.execute_script('return processing_geometries_missing_l2a;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l2a, map_l2a_missing_tooltip_info)

        # Check whether the timeline is displayed
        timeline_section = self.driver.find_element_by_id("processing-timeline-section")

        condition = timeline_section.is_displayed()
        assert condition is True

        # Check timeline segments tooltip
        # Complete
        complete_timeline_tooltip_info = []

        returned_complete_processing_timeline = self.driver.execute_script('return complete_processing_timeline;')
        assert complete_timeline_tooltip_info == returned_complete_processing_timeline
        # Missing
        missing_timeline_tooltip_info = [
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l0[0].event_uuid),
                "start": "2021-02-22T16:11:01.232404",
                "stop": "2021-02-22T16:20:49.409987",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l0[1].event_uuid),
                "start": "2021-02-22T16:23:16.158836",
                "stop": "2021-02-22T16:24:11.642258",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l0[2].event_uuid),
                "start": "2021-02-22T16:43:54.133697",
                "stop": "2021-02-22T16:45:08.443523",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },     
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1b[0].event_uuid),
                "start": "2021-02-22T16:11:01.232404",
                "stop": "2021-02-22T16:20:49.409987",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1b[1].event_uuid),
                "start": "2021-02-22T16:23:16.158836",
                "stop": "2021-02-22T16:24:11.642258",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1b[2].event_uuid),
                "start": "2021-02-22T16:43:54.133697",
                "stop": "2021-02-22T16:45:08.443523",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1c[0].event_uuid),
                "start": "2021-02-22T16:11:01.232404",
                "stop": "2021-02-22T16:20:49.409987",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1c[1].event_uuid),
                "start": "2021-02-22T16:23:16.158836",
                "stop": "2021-02-22T16:24:11.642258",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1c[2].event_uuid),
                "start": "2021-02-22T16:43:54.133697",
                "stop": "2021-02-22T16:45:08.443523",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l2a[0].event_uuid),
                "start": "2021-02-22T16:11:01.232404",
                "stop": "2021-02-22T16:20:49.409987",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l2a[1].event_uuid),
                "start": "2021-02-22T16:23:16.158836",
                "stop": "2021-02-22T16:24:11.642258",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l2a[2].event_uuid),
                "start": "2021-02-22T16:43:54.133697",
                "stop": "2021-02-22T16:45:08.443523",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
        ]

        returned_missing_processing_timeline = self.driver.execute_script('return missing_processing_timeline;')
        functions_vboa.verify_js_var(returned_missing_processing_timeline, missing_timeline_tooltip_info)

        # Incomplete
        incomplete_timeline_tooltip_info = []

        returned_incomplete_processing_timeline = self.driver.execute_script('return incomplete_processing_timeline;')
        assert incomplete_timeline_tooltip_info == returned_incomplete_processing_timeline

        # Check processing missing table
        missing_table = self.driver.find_element_by_id("processing-missing-table")

        # Row 1
        satellite = missing_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 2
        satellite = missing_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 3
        satellite = missing_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 4
        satellite = missing_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 5
        satellite = missing_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_table.find_element_by_xpath("tbody/tr[5]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[5]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"
        
        # Row 6
        satellite = missing_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_table.find_element_by_xpath("tbody/tr[6]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[6]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 7
        satellite = missing_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_table.find_element_by_xpath("tbody/tr[7]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[7]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 8
        satellite = missing_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_table.find_element_by_xpath("tbody/tr[8]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_table.find_element_by_xpath("tbody/tr[8]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[8]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

         # Row 9
        satellite = missing_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_table.find_element_by_xpath("tbody/tr[9]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_table.find_element_by_xpath("tbody/tr[9]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[9]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 10
        satellite = missing_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_table.find_element_by_xpath("tbody/tr[10]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_table.find_element_by_xpath("tbody/tr[10]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[10]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

         # Row 11
        satellite = missing_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_table.find_element_by_xpath("tbody/tr[11]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_table.find_element_by_xpath("tbody/tr[11]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[11]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

         # Row 12
        satellite = missing_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_table.find_element_by_xpath("tbody/tr[12]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_table.find_element_by_xpath("tbody/tr[12]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[12]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"
        
        # Check processing completeness table
        completeness_table = self.driver.find_element_by_id("processing-completeness-table")

        # Row 1
        satellite = completeness_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 2
        satellite = completeness_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 3
        satellite = completeness_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 4
        satellite = completeness_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 5
        satellite = completeness_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_table.find_element_by_xpath("tbody/tr[5]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[5]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"
        
        # Row 6
        satellite = completeness_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_table.find_element_by_xpath("tbody/tr[6]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[6]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 7
        satellite = completeness_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "N/A"
        
        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_table.find_element_by_xpath("tbody/tr[7]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[7]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 8
        satellite = completeness_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_table.find_element_by_xpath("tbody/tr[8]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_table.find_element_by_xpath("tbody/tr[8]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[8]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

         # Row 9
        satellite = completeness_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_table.find_element_by_xpath("tbody/tr[9]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_table.find_element_by_xpath("tbody/tr[9]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[9]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 10
        satellite = completeness_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_table.find_element_by_xpath("tbody/tr[10]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_table.find_element_by_xpath("tbody/tr[10]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[10]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

         # Row 11
        satellite = completeness_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_table.find_element_by_xpath("tbody/tr[11]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_table.find_element_by_xpath("tbody/tr[11]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[11]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

         # Row 12
        satellite = completeness_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_table.find_element_by_xpath("tbody/tr[12]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_table.find_element_by_xpath("tbody/tr[12]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[12]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Datastrip by UUID completeness table
        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/specific-processing/" + str(planned_playback[0].event_uuid))

        # Check summary pies
        # L0
        processing_data_l0_pie_info = [0,3]

        returned_processing_data_l0_pie_info = self.driver.execute_script('return processing_data_l0;')
        assert processing_data_l0_pie_info == returned_processing_data_l0_pie_info

        # L1B
        processing_data_l1b_pie_info = [0,3]

        returned_processing_data_l1b_pie_info = self.driver.execute_script('return processing_data_l1b;')
        assert processing_data_l1b_pie_info == returned_processing_data_l1b_pie_info

        # L1C
        processing_data_l1c_pie_info = [0,3]

        returned_processing_data_l1c_pie_info = self.driver.execute_script('return processing_data_l1c;')
        assert processing_data_l1c_pie_info == returned_processing_data_l1c_pie_info
        
        # L2A
        processing_data_l2a_pie_info = [0,3]

        returned_processing_data_l2a_pie_info = self.driver.execute_script('return processing_data_l2a;')
        assert processing_data_l2a_pie_info == returned_processing_data_l2a_pie_info
        
        # Check summary expected playbacks
        summary_expected_playbacks = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-playbacks")))

        assert summary_expected_playbacks

        assert summary_expected_playbacks.text == "1"

        # Check summary expected datastrips
        summary_expected_datastrips = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-datastrips")))

        assert summary_expected_datastrips

        assert summary_expected_datastrips.text == "3"

        # Check summary expected missing processing L0
        summary_expected_missing_processing_l0 = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l0")))

        assert summary_expected_missing_processing_l0

        assert summary_expected_missing_processing_l0.text == "3"

        # Check summary expected missing processing L1B
        summary_expected_missing_processing_l1b = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1b")))

        assert summary_expected_missing_processing_l1b

        assert summary_expected_missing_processing_l1b.text == "3"

        # Check summary expected missing processing L1C
        summary_expected_missing_processing_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1c")))

        assert summary_expected_missing_processing_l1c

        assert summary_expected_missing_processing_l1c.text == "3"

        # Check summary expected missing processing L2A
        summary_expected_missing_processing_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l2a")))

        assert summary_expected_missing_processing_l2a

        assert summary_expected_missing_processing_l2a.text == "3"

        # Check summary processing table
        summary_table = self.driver.find_element_by_id("summary-processing-table")

        # Row 1
        level = summary_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L0"

        expected = summary_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert performance.text == "0.0"

        # Row 2
        level = summary_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1B"

        expected = summary_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert performance.text == "0.0"

        # Row 3
        level = summary_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L1C"

        expected = summary_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert performance.text == "0.0"

        # Row 4
        level = summary_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert level.text == "L2A"

        expected = summary_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert performance.text == "0.0"
        
        # Check processing missing table
        missing_datastrip_table = self.driver.find_element_by_id("processing-missing-table")

        # Row 1
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 2
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 3
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 4
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 5
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"
        
        # Row 6
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 7
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 8
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

         # Row 9
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 10
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

         # Row 11
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

         # Row 12
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Check processing missing table
        completeness_datastrip_table = self.driver.find_element_by_id("processing-completeness-table")

        # Row 1
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 2
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 3
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 4
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 5
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"
        
        # Row 6
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 7
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 8
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

         # Row 9
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

        # Row 10
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

         # Row 11
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

         # Row 12
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[12]")

        assert sad_coverage.text == "2021-02-22T05:54:39.024895_2021-02-22T19:22:49.024749"

    def test_processing_with_rep_pass_e_vgs_partial_sad(self):

        filename = "S2B_OPER_MPL__NPPF__20210218T120000_20210308T150000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_MPL_ORBPRE_20210221T030153_20210303T030153_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_MPL_SPSGS__PDMC_20210221T090000_V20210222T090000_20210228T090000.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_REP_PASS_E_VGS2_20210222T193404_V20210222T191105_20210222T191846.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_REP_PASS_E_VGS2_20210222T193412_V20210222T191106_20210222T191854_PARTIAL_SAD.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/processing")

        functions.query(self.driver, wait, "S2B", start = "2021-02-18T12:00:00", stop = "2021-03-08T15:00:00", start_orbit = "20706", stop_orbit = "20720", map = True, timeline = True)

        # Check summary pies
        # L0
        processing_data_l0_pie_info = [0,3]

        returned_processing_data_l0_pie_info = self.driver.execute_script('return processing_data_l0;')
        assert processing_data_l0_pie_info == returned_processing_data_l0_pie_info

        # L1B
        processing_data_l1b_pie_info = [0,3]

        returned_processing_data_l1b_pie_info = self.driver.execute_script('return processing_data_l1b;')
        assert processing_data_l1b_pie_info == returned_processing_data_l1b_pie_info

        # L1C
        processing_data_l1c_pie_info = [0,3]

        returned_processing_data_l1c_pie_info = self.driver.execute_script('return processing_data_l1c;')
        assert processing_data_l1c_pie_info == returned_processing_data_l1c_pie_info
        
        # L2A
        processing_data_l2a_pie_info = [0,3]

        returned_processing_data_l2a_pie_info = self.driver.execute_script('return processing_data_l2a;')
        assert processing_data_l2a_pie_info == returned_processing_data_l2a_pie_info
        
        # Check summary expected playbacks
        summary_expected_playbacks = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-playbacks")))

        assert summary_expected_playbacks

        assert summary_expected_playbacks.text == "1"

        # Check summary expected datastrips
        summary_expected_datastrips = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-datastrips")))

        assert summary_expected_datastrips

        assert summary_expected_datastrips.text == "3"

        # Check summary expected missing processing L0
        summary_expected_missing_processing_l0 = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l0")))

        assert summary_expected_missing_processing_l0

        assert summary_expected_missing_processing_l0.text == "3"

        # Check summary expected missing processing L1B
        summary_expected_missing_processing_l1b = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1b")))

        assert summary_expected_missing_processing_l1b

        assert summary_expected_missing_processing_l1b.text == "3"

        # Check summary expected missing processing L1C
        summary_expected_missing_processing_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1c")))

        assert summary_expected_missing_processing_l1c

        assert summary_expected_missing_processing_l1c.text == "3"

        # Check summary expected missing processing L2A
        summary_expected_missing_processing_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l2a")))

        assert summary_expected_missing_processing_l2a

        assert summary_expected_missing_processing_l2a.text == "3"

        # Check summary processing table
        summary_table = self.driver.find_element_by_id("summary-processing-table")

        # Row 1
        level = summary_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L0"

        expected = summary_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert performance.text == "0.0"

        # Row 2
        level = summary_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1B"

        expected = summary_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert performance.text == "0.0"

        # Row 3
        level = summary_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L1C"

        expected = summary_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert performance.text == "0.0"

        # Row 4
        level = summary_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert level.text == "L2A"

        expected = summary_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert performance.text == "0.0"

        # Check whether the maps are displayed
        map_section = self.driver.find_element_by_id("processing-on-map-section")

        condition = map_section.is_displayed()

        assert condition is True
        
        # Check map complete segments tooltip
        planned_playback_correction = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_CORRECTION", "op":"=="},
                                                                start_filters =[{"date": "2021-02-22T19:11:03.543116", "op":"=="}],
                                                                stop_filters = [{"date": "2021-02-22T19:22:43.099034", "op": "=="}])
        sad_data = self.query_eboa.get_events(gauge_names ={"filter": "SAD_DATA", "op":"=="})
        isp_validity = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY", "op":"=="},
                                                  value_filters = [{"name": {"op": "==", "filter": "channel"},
                                                                    "type": "double",
                                                                    "value": {"op": "==", "filter": "2"}}],
                                                  order_by = {"field": "start", "descending": False})
        planned_playback = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"=="},
                                                    start_filters =[{"date": "2021-02-22T19:11:01.731000", "op":"=="}],
                                                    stop_filters = [{"date": "2021-02-22T19:22:40.627000", "op": "=="}])
        # L0
        isp_validity_processing_completeness_l0 = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0_CHANNEL_2", "op":"=="},
                                                                             order_by = {"field": "start", "descending": False})
        
        map_l0_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l0[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l0[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>PARTIAL_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l0[1].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l0[1].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l0[2].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l0[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l0 = self.driver.execute_script('return processing_geometries_missing_l0;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l0, map_l0_missing_tooltip_info)

        # L1B
        isp_validity_processing_completeness_l1b = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1B_CHANNEL_2", "op":"=="},
                                                                             order_by = {"field": "start", "descending": False})
        
        map_l1b_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l1b[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1b[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>PARTIAL_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l1b[1].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1b[1].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l1b[2].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1b[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l1b = self.driver.execute_script('return processing_geometries_missing_l1b;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l1b, map_l1b_missing_tooltip_info)

        # L1C
        isp_validity_processing_completeness_l1c = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1C_CHANNEL_2", "op":"=="},
                                                                             order_by = {"field": "start", "descending": False})
        
        map_l1c_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l1c[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1c[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>PARTIAL_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l1c[1].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1c[1].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l1c[2].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1c[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l1c = self.driver.execute_script('return processing_geometries_missing_l1c;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l1c, map_l1c_missing_tooltip_info)

        # L2A
        isp_validity_processing_completeness_l2a = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L2A_CHANNEL_2", "op":"=="},
                                                                             order_by = {"field": "start", "descending": False})
        
        map_l2a_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l2a[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l2a[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>PARTIAL_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l2a[1].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l2a[1].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l2a[2].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l2a[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l2a = self.driver.execute_script('return processing_geometries_missing_l2a;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l2a, map_l2a_missing_tooltip_info)

        # Check whether the timeline is displayed
        timeline_section = self.driver.find_element_by_id("processing-timeline-section")

        condition = timeline_section.is_displayed()
        assert condition is True

        # Check timeline segments tooltip
        # Complete
        complete_timeline_tooltip_info = []

        returned_complete_processing_timeline = self.driver.execute_script('return complete_processing_timeline;')
        assert complete_timeline_tooltip_info == returned_complete_processing_timeline
        # Missing
        missing_timeline_tooltip_info = [
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l0[0].event_uuid),
                "start": "2021-02-22T16:11:01.232404",
                "stop": "2021-02-22T16:20:49.409987",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>PARTIAL_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l0[1].event_uuid),
                "start": "2021-02-22T16:23:16.158836",
                "stop": "2021-02-22T16:24:11.642258",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l0[2].event_uuid),
                "start": "2021-02-22T16:43:54.133697",
                "stop": "2021-02-22T16:45:08.443523",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },     
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1b[0].event_uuid),
                "start": "2021-02-22T16:11:01.232404",
                "stop": "2021-02-22T16:20:49.409987",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>PARTIAL_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1b[1].event_uuid),
                "start": "2021-02-22T16:23:16.158836",
                "stop": "2021-02-22T16:24:11.642258",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1b[2].event_uuid),
                "start": "2021-02-22T16:43:54.133697",
                "stop": "2021-02-22T16:45:08.443523",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1c[0].event_uuid),
                "start": "2021-02-22T16:11:01.232404",
                "stop": "2021-02-22T16:20:49.409987",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>PARTIAL_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1c[1].event_uuid),
                "start": "2021-02-22T16:23:16.158836",
                "stop": "2021-02-22T16:24:11.642258",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1c[2].event_uuid),
                "start": "2021-02-22T16:43:54.133697",
                "stop": "2021-02-22T16:45:08.443523",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l2a[0].event_uuid),
                "start": "2021-02-22T16:11:01.232404",
                "stop": "2021-02-22T16:20:49.409987",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>PARTIAL_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l2a[1].event_uuid),
                "start": "2021-02-22T16:23:16.158836",
                "stop": "2021-02-22T16:24:11.642258",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l2a[2].event_uuid),
                "start": "2021-02-22T16:43:54.133697",
                "stop": "2021-02-22T16:45:08.443523",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749</a></td></tr>" +
                "</table>"
            },
        ]

        returned_missing_processing_timeline = self.driver.execute_script('return missing_processing_timeline;')
        functions_vboa.verify_js_var(returned_missing_processing_timeline, missing_timeline_tooltip_info)

        # Incomplete
        incomplete_timeline_tooltip_info = []

        returned_incomplete_processing_timeline = self.driver.execute_script('return incomplete_processing_timeline;')
        assert incomplete_timeline_tooltip_info == returned_incomplete_processing_timeline

        # Check processing missing table
        missing_table = self.driver.find_element_by_id("processing-missing-table")

        # Row 1
        satellite = missing_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 2
        satellite = missing_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 3
        satellite = missing_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 4
        satellite = missing_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 5
        satellite = missing_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_table.find_element_by_xpath("tbody/tr[5]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[5]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"
        
        # Row 6
        satellite = missing_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_table.find_element_by_xpath("tbody/tr[6]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[6]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 7
        satellite = missing_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_table.find_element_by_xpath("tbody/tr[7]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[7]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 8
        satellite = missing_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_table.find_element_by_xpath("tbody/tr[8]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_table.find_element_by_xpath("tbody/tr[8]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[8]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

         # Row 9
        satellite = missing_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_table.find_element_by_xpath("tbody/tr[9]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_table.find_element_by_xpath("tbody/tr[9]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[9]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 10
        satellite = missing_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_table.find_element_by_xpath("tbody/tr[10]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_table.find_element_by_xpath("tbody/tr[10]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[10]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

         # Row 11
        satellite = missing_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_table.find_element_by_xpath("tbody/tr[11]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_table.find_element_by_xpath("tbody/tr[11]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[11]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

         # Row 12
        satellite = missing_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_table.find_element_by_xpath("tbody/tr[12]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_table.find_element_by_xpath("tbody/tr[12]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[12]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"
        
        # Check processing completeness table
        completeness_table = self.driver.find_element_by_id("processing-completeness-table")

        # Row 1
        satellite = completeness_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 2
        satellite = completeness_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 3
        satellite = completeness_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 4
        satellite = completeness_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 5
        satellite = completeness_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_table.find_element_by_xpath("tbody/tr[5]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[5]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"
        
        # Row 6
        satellite = completeness_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_table.find_element_by_xpath("tbody/tr[6]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[6]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 7
        satellite = completeness_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "N/A"
        
        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_table.find_element_by_xpath("tbody/tr[7]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[7]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 8
        satellite = completeness_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_table.find_element_by_xpath("tbody/tr[8]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_table.find_element_by_xpath("tbody/tr[8]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[8]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

         # Row 9
        satellite = completeness_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_table.find_element_by_xpath("tbody/tr[9]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_table.find_element_by_xpath("tbody/tr[9]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[9]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 10
        satellite = completeness_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_table.find_element_by_xpath("tbody/tr[10]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_table.find_element_by_xpath("tbody/tr[10]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[10]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

         # Row 11
        satellite = completeness_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_table.find_element_by_xpath("tbody/tr[11]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_table.find_element_by_xpath("tbody/tr[11]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[11]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

         # Row 12
        satellite = completeness_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_table.find_element_by_xpath("tbody/tr[12]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_table.find_element_by_xpath("tbody/tr[12]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[12]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Datastrip by UUID completeness table
        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/specific-processing/" + str(planned_playback[0].event_uuid))

        # Check summary pies
        # L0
        processing_data_l0_pie_info = [0,3]

        returned_processing_data_l0_pie_info = self.driver.execute_script('return processing_data_l0;')
        assert processing_data_l0_pie_info == returned_processing_data_l0_pie_info

        # L1B
        processing_data_l1b_pie_info = [0,3]

        returned_processing_data_l1b_pie_info = self.driver.execute_script('return processing_data_l1b;')
        assert processing_data_l1b_pie_info == returned_processing_data_l1b_pie_info

        # L1C
        processing_data_l1c_pie_info = [0,3]

        returned_processing_data_l1c_pie_info = self.driver.execute_script('return processing_data_l1c;')
        assert processing_data_l1c_pie_info == returned_processing_data_l1c_pie_info
        
        # L2A
        processing_data_l2a_pie_info = [0,3]

        returned_processing_data_l2a_pie_info = self.driver.execute_script('return processing_data_l2a;')
        assert processing_data_l2a_pie_info == returned_processing_data_l2a_pie_info
        
        # Check summary expected playbacks
        summary_expected_playbacks = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-playbacks")))

        assert summary_expected_playbacks

        assert summary_expected_playbacks.text == "1"

        # Check summary expected datastrips
        summary_expected_datastrips = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-datastrips")))

        assert summary_expected_datastrips

        assert summary_expected_datastrips.text == "3"

        # Check summary expected missing processing L0
        summary_expected_missing_processing_l0 = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l0")))

        assert summary_expected_missing_processing_l0

        assert summary_expected_missing_processing_l0.text == "3"

        # Check summary expected missing processing L1B
        summary_expected_missing_processing_l1b = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1b")))

        assert summary_expected_missing_processing_l1b

        assert summary_expected_missing_processing_l1b.text == "3"

        # Check summary expected missing processing L1C
        summary_expected_missing_processing_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1c")))

        assert summary_expected_missing_processing_l1c

        assert summary_expected_missing_processing_l1c.text == "3"

        # Check summary expected missing processing L2A
        summary_expected_missing_processing_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l2a")))

        assert summary_expected_missing_processing_l2a

        assert summary_expected_missing_processing_l2a.text == "3"

        # Check summary processing table
        summary_table = self.driver.find_element_by_id("summary-processing-table")

        # Row 1
        level = summary_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L0"

        expected = summary_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert performance.text == "0.0"

        # Row 2
        level = summary_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1B"

        expected = summary_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert performance.text == "0.0"

        # Row 3
        level = summary_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L1C"

        expected = summary_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert performance.text == "0.0"

        # Row 4
        level = summary_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert level.text == "L2A"

        expected = summary_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert performance.text == "0.0"
        
        # Check processing missing table
        missing_datastrip_table = self.driver.find_element_by_id("processing-missing-table")

        # Row 1
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 2
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 3
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 4
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 5
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"
        
        # Row 6
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 7
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 8
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

         # Row 9
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 10
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

         # Row 11
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

         # Row 12
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Check processing missing table
        completeness_datastrip_table = self.driver.find_element_by_id("processing-completeness-table")

        # Row 1
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 2
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 3
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 4
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "PARTIAL_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 5
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"
        
        # Row 6
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 7
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 8
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

         # Row 9
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

        # Row 10
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

         # Row 11
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

         # Row 12
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[12]")

        assert sad_coverage.text == "2021-02-22T16:15:39.024895_2021-02-22T19:22:49.024749"

    def test_processing_with_rep_pass_e_vgs_missing_sad(self):

        filename = "S2B_OPER_MPL__NPPF__20210218T120000_20210308T150000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_MPL_ORBPRE_20210221T030153_20210303T030153_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_MPL_SPSGS__PDMC_20210221T090000_V20210222T090000_20210228T090000.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_REP_PASS_E_VGS2_20210222T193404_V20210222T191105_20210222T191846.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_REP_PASS_E_VGS2_20210222T193412_V20210222T191106_20210222T191854_MISSING_SAD.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/processing")

        functions.query(self.driver, wait, "S2B", start = "2021-02-18T12:00:00", stop = "2021-03-08T15:00:00", start_orbit = "20706", stop_orbit = "20720", map = True, timeline = True)

        # Check summary pies
        # L0
        processing_data_l0_pie_info = [0,3]

        returned_processing_data_l0_pie_info = self.driver.execute_script('return processing_data_l0;')
        assert processing_data_l0_pie_info == returned_processing_data_l0_pie_info

        # L1B
        processing_data_l1b_pie_info = [0,3]

        returned_processing_data_l1b_pie_info = self.driver.execute_script('return processing_data_l1b;')
        assert processing_data_l1b_pie_info == returned_processing_data_l1b_pie_info

        # L1C
        processing_data_l1c_pie_info = [0,3]

        returned_processing_data_l1c_pie_info = self.driver.execute_script('return processing_data_l1c;')
        assert processing_data_l1c_pie_info == returned_processing_data_l1c_pie_info
        
        # L2A
        processing_data_l2a_pie_info = [0,3]

        returned_processing_data_l2a_pie_info = self.driver.execute_script('return processing_data_l2a;')
        assert processing_data_l2a_pie_info == returned_processing_data_l2a_pie_info
        
        # Check summary expected playbacks
        summary_expected_playbacks = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-playbacks")))

        assert summary_expected_playbacks

        assert summary_expected_playbacks.text == "1"

        # Check summary expected datastrips
        summary_expected_datastrips = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-datastrips")))

        assert summary_expected_datastrips

        assert summary_expected_datastrips.text == "3"

        # Check summary expected missing processing L0
        summary_expected_missing_processing_l0 = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l0")))

        assert summary_expected_missing_processing_l0

        assert summary_expected_missing_processing_l0.text == "3"

        # Check summary expected missing processing L1B
        summary_expected_missing_processing_l1b = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1b")))

        assert summary_expected_missing_processing_l1b

        assert summary_expected_missing_processing_l1b.text == "3"

        # Check summary expected missing processing L1C
        summary_expected_missing_processing_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1c")))

        assert summary_expected_missing_processing_l1c

        assert summary_expected_missing_processing_l1c.text == "3"

        # Check summary expected missing processing L2A
        summary_expected_missing_processing_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l2a")))

        assert summary_expected_missing_processing_l2a

        assert summary_expected_missing_processing_l2a.text == "3"

        # Check summary processing table
        summary_table = self.driver.find_element_by_id("summary-processing-table")

        # Row 1
        level = summary_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L0"

        expected = summary_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert performance.text == "0.0"

        # Row 2
        level = summary_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1B"

        expected = summary_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert performance.text == "0.0"

        # Row 3
        level = summary_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L1C"

        expected = summary_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert performance.text == "0.0"

        # Row 4
        level = summary_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert level.text == "L2A"

        expected = summary_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert performance.text == "0.0"

        # Check whether the maps are displayed
        map_section = self.driver.find_element_by_id("processing-on-map-section")

        condition = map_section.is_displayed()

        assert condition is True
        
        # Check map complete segments tooltip
        planned_playback_correction = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK_CORRECTION", "op":"=="},
                                                                start_filters =[{"date": "2021-02-22T19:11:03.543116", "op":"=="}],
                                                                stop_filters = [{"date": "2021-02-22T19:22:43.099034", "op": "=="}])
        isp_validity = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY", "op":"=="},
                                                  value_filters = [{"name": {"op": "==", "filter": "channel"},
                                                                    "type": "double",
                                                                    "value": {"op": "==", "filter": "2"}}],
                                                  order_by = {"field": "start", "descending": False})
        planned_playback = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"=="},
                                                    start_filters =[{"date": "2021-02-22T19:11:01.731000", "op":"=="}],
                                                    stop_filters = [{"date": "2021-02-22T19:22:40.627000", "op": "=="}])
        # L0
        isp_validity_processing_completeness_l0 = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0_CHANNEL_2", "op":"=="},
                                                                             order_by = {"field": "start", "descending": False})
        
        map_l0_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l0[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l0[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l0[1].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l0[1].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l0[2].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l0[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l0 = self.driver.execute_script('return processing_geometries_missing_l0;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l0, map_l0_missing_tooltip_info)

        # L1B
        isp_validity_processing_completeness_l1b = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1B_CHANNEL_2", "op":"=="},
                                                                             order_by = {"field": "start", "descending": False})
        
        map_l1b_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l1b[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1b[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l1b[1].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1b[1].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l1b[2].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1b[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l1b = self.driver.execute_script('return processing_geometries_missing_l1b;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l1b, map_l1b_missing_tooltip_info)

        # L1C
        isp_validity_processing_completeness_l1c = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1C_CHANNEL_2", "op":"=="},
                                                                             order_by = {"field": "start", "descending": False})
        
        map_l1c_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l1c[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1c[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l1c[1].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1c[1].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l1c[2].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l1c[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l1c = self.driver.execute_script('return processing_geometries_missing_l1c;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l1c, map_l1c_missing_tooltip_info)

        # L2A
        isp_validity_processing_completeness_l2a = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L2A_CHANNEL_2", "op":"=="},
                                                                             order_by = {"field": "start", "descending": False})
        
        map_l2a_missing_tooltip_info = [
            {
                "geometries": [
                        isp_validity_processing_completeness_l2a[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l2a[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l2a[1].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l2a[1].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_validity_processing_completeness_l2a[2].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_validity_processing_completeness_l2a[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_missing_l2a = self.driver.execute_script('return processing_geometries_missing_l2a;')
        functions_vboa.verify_js_var(returned_processing_geometries_missing_l2a, map_l2a_missing_tooltip_info)

        # Check whether the timeline is displayed
        timeline_section = self.driver.find_element_by_id("processing-timeline-section")

        condition = timeline_section.is_displayed()
        assert condition is True

        # Check timeline segments tooltip
        # Complete
        complete_timeline_tooltip_info = []

        returned_complete_processing_timeline = self.driver.execute_script('return complete_processing_timeline;')
        assert complete_timeline_tooltip_info == returned_complete_processing_timeline
        # Missing
        missing_timeline_tooltip_info = [
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l0[0].event_uuid),
                "start": "2021-02-22T16:11:01.232404",
                "stop": "2021-02-22T16:20:49.409987",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l0[1].event_uuid),
                "start": "2021-02-22T16:23:16.158836",
                "stop": "2021-02-22T16:24:11.642258",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l0[2].event_uuid),
                "start": "2021-02-22T16:43:54.133697",
                "stop": "2021-02-22T16:45:08.443523",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l0[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l0[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l0[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l0[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },     
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1b[0].event_uuid),
                "start": "2021-02-22T16:11:01.232404",
                "stop": "2021-02-22T16:20:49.409987",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1b[1].event_uuid),
                "start": "2021-02-22T16:23:16.158836",
                "stop": "2021-02-22T16:24:11.642258",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1b[2].event_uuid),
                "start": "2021-02-22T16:43:54.133697",
                "stop": "2021-02-22T16:45:08.443523",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1b[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1b[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1b[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1b[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1c[0].event_uuid),
                "start": "2021-02-22T16:11:01.232404",
                "stop": "2021-02-22T16:20:49.409987",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1c[1].event_uuid),
                "start": "2021-02-22T16:23:16.158836",
                "stop": "2021-02-22T16:24:11.642258",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l1c[2].event_uuid),
                "start": "2021-02-22T16:43:54.133697",
                "stop": "2021-02-22T16:45:08.443523",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l1c[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l1c[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l1c[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l1c[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l2a[0].event_uuid),
                "start": "2021-02-22T16:11:01.232404",
                "stop": "2021-02-22T16:20:49.409987",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>9.803</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l2a[1].event_uuid),
                "start": "2021-02-22T16:23:16.158836",
                "stop": "2021-02-22T16:24:11.642258",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[1].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>0.925</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2B;SGS_",
                "id": str(isp_validity_processing_completeness_l2a[2].event_uuid),
                "start": "2021-02-22T16:43:54.133697",
                "stop": "2021-02-22T16:45:08.443523",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_validity_processing_completeness_l2a[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2B</td></tr>" + 
                "<tr><td>Downlink orbit</td><td><a href='/views/specific-acquisition/" + str(planned_playback_correction[0].event_uuid) + "'>20717.0</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>20715</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(planned_playback[0].event_uuid) + "' class=bold-red>MISSING_SAD</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_validity_processing_completeness_l2a[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + isp_validity_processing_completeness_l2a[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_validity_processing_completeness_l2a[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.238</td></tr>" +
                "<tr><td>SAD coverage</td><td>N/A</td></tr>" +
                "</table>"
            },
        ]

        returned_missing_processing_timeline = self.driver.execute_script('return missing_processing_timeline;')
        functions_vboa.verify_js_var(returned_missing_processing_timeline, missing_timeline_tooltip_info)

        # Incomplete
        incomplete_timeline_tooltip_info = []

        returned_incomplete_processing_timeline = self.driver.execute_script('return incomplete_processing_timeline;')
        assert incomplete_timeline_tooltip_info == returned_incomplete_processing_timeline

        # Check processing missing table
        missing_table = self.driver.find_element_by_id("processing-missing-table")

        # Row 1
        satellite = missing_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 2
        satellite = missing_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 3
        satellite = missing_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 4
        satellite = missing_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 5
        satellite = missing_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_table.find_element_by_xpath("tbody/tr[5]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[5]/td[12]")

        assert sad_coverage.text == "N/A"
        
        # Row 6
        satellite = missing_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_table.find_element_by_xpath("tbody/tr[6]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[6]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 7
        satellite = missing_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_table.find_element_by_xpath("tbody/tr[7]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[7]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 8
        satellite = missing_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_table.find_element_by_xpath("tbody/tr[8]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_table.find_element_by_xpath("tbody/tr[8]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[8]/td[12]")

        assert sad_coverage.text == "N/A"

         # Row 9
        satellite = missing_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_table.find_element_by_xpath("tbody/tr[9]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_table.find_element_by_xpath("tbody/tr[9]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[9]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 10
        satellite = missing_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_table.find_element_by_xpath("tbody/tr[10]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_table.find_element_by_xpath("tbody/tr[10]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[10]/td[12]")

        assert sad_coverage.text == "N/A"

         # Row 11
        satellite = missing_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_table.find_element_by_xpath("tbody/tr[11]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_table.find_element_by_xpath("tbody/tr[11]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[11]/td[12]")

        assert sad_coverage.text == "N/A"

         # Row 12
        satellite = missing_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert station.text == "SGS_"

        level = missing_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_table.find_element_by_xpath("tbody/tr[12]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_table.find_element_by_xpath("tbody/tr[12]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_table.find_element_by_xpath("tbody/tr[12]/td[12]")

        assert sad_coverage.text == "N/A"
        
        # Check processing completeness table
        completeness_table = self.driver.find_element_by_id("processing-completeness-table")

        # Row 1
        satellite = completeness_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 2
        satellite = completeness_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 3
        satellite = completeness_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 4
        satellite = completeness_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 5
        satellite = completeness_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_table.find_element_by_xpath("tbody/tr[5]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[5]/td[12]")

        assert sad_coverage.text == "N/A"
        
        # Row 6
        satellite = completeness_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_table.find_element_by_xpath("tbody/tr[6]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[6]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 7
        satellite = completeness_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "N/A"
        
        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_table.find_element_by_xpath("tbody/tr[7]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[7]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 8
        satellite = completeness_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_table.find_element_by_xpath("tbody/tr[8]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_table.find_element_by_xpath("tbody/tr[8]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[8]/td[12]")

        assert sad_coverage.text == "N/A"

         # Row 9
        satellite = completeness_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_table.find_element_by_xpath("tbody/tr[9]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_table.find_element_by_xpath("tbody/tr[9]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[9]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 10
        satellite = completeness_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_table.find_element_by_xpath("tbody/tr[10]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_table.find_element_by_xpath("tbody/tr[10]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[10]/td[12]")

        assert sad_coverage.text == "N/A"

         # Row 11
        satellite = completeness_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_table.find_element_by_xpath("tbody/tr[11]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_table.find_element_by_xpath("tbody/tr[11]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[11]/td[12]")

        assert sad_coverage.text == "N/A"

         # Row 12
        satellite = completeness_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert station.text == "SGS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_table.find_element_by_xpath("tbody/tr[12]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_table.find_element_by_xpath("tbody/tr[12]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[12]/td[12]")

        assert sad_coverage.text == "N/A"

        # Datastrip by UUID completeness table
        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/specific-processing/" + str(planned_playback[0].event_uuid))

        # Check summary pies
        # L0
        processing_data_l0_pie_info = [0,3]

        returned_processing_data_l0_pie_info = self.driver.execute_script('return processing_data_l0;')
        assert processing_data_l0_pie_info == returned_processing_data_l0_pie_info

        # L1B
        processing_data_l1b_pie_info = [0,3]

        returned_processing_data_l1b_pie_info = self.driver.execute_script('return processing_data_l1b;')
        assert processing_data_l1b_pie_info == returned_processing_data_l1b_pie_info

        # L1C
        processing_data_l1c_pie_info = [0,3]

        returned_processing_data_l1c_pie_info = self.driver.execute_script('return processing_data_l1c;')
        assert processing_data_l1c_pie_info == returned_processing_data_l1c_pie_info
        
        # L2A
        processing_data_l2a_pie_info = [0,3]

        returned_processing_data_l2a_pie_info = self.driver.execute_script('return processing_data_l2a;')
        assert processing_data_l2a_pie_info == returned_processing_data_l2a_pie_info
        
        # Check summary expected playbacks
        summary_expected_playbacks = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-playbacks")))

        assert summary_expected_playbacks

        assert summary_expected_playbacks.text == "1"

        # Check summary expected datastrips
        summary_expected_datastrips = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-datastrips")))

        assert summary_expected_datastrips

        assert summary_expected_datastrips.text == "3"

        # Check summary expected missing processing L0
        summary_expected_missing_processing_l0 = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l0")))

        assert summary_expected_missing_processing_l0

        assert summary_expected_missing_processing_l0.text == "3"

        # Check summary expected missing processing L1B
        summary_expected_missing_processing_l1b = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1b")))

        assert summary_expected_missing_processing_l1b

        assert summary_expected_missing_processing_l1b.text == "3"

        # Check summary expected missing processing L1C
        summary_expected_missing_processing_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l1c")))

        assert summary_expected_missing_processing_l1c

        assert summary_expected_missing_processing_l1c.text == "3"

        # Check summary expected missing processing L2A
        summary_expected_missing_processing_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-processing-missing-l2a")))

        assert summary_expected_missing_processing_l2a

        assert summary_expected_missing_processing_l2a.text == "3"

        # Check summary processing table
        summary_table = self.driver.find_element_by_id("summary-processing-table")

        # Row 1
        level = summary_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L0"

        expected = summary_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert performance.text == "0.0"

        # Row 2
        level = summary_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1B"

        expected = summary_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert performance.text == "0.0"

        # Row 3
        level = summary_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L1C"

        expected = summary_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert performance.text == "0.0"

        # Row 4
        level = summary_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert level.text == "L2A"

        expected = summary_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert expected.text == "3"

        missing = summary_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert missing.text == "3"

        incomplete = summary_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert incomplete.text == "0"

        performance = summary_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert performance.text == "0.0"
        
        # Check processing missing table
        missing_datastrip_table = self.driver.find_element_by_id("processing-missing-table")

        # Row 1
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 2
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 3
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 4
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 5
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[12]")

        assert sad_coverage.text == "N/A"
        
        # Row 6
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 7
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 8
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[12]")

        assert sad_coverage.text == "N/A"

         # Row 9
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert level.text == "L0"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 10
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[12]")

        assert sad_coverage.text == "N/A"

         # Row 11
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[12]")

        assert sad_coverage.text == "N/A"

         # Row 12
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert station.text == "SGS_"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = missing_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[12]")

        assert sad_coverage.text == "N/A"

        # Check processing missing table
        completeness_datastrip_table = self.driver.find_element_by_id("processing-completeness-table")

        # Row 1
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 2
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 3
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 4
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert start.text == "2021-02-22T16:11:01.232404"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert stop.text == "2021-02-22T16:20:49.409987"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert duration.text == "9.803"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 5
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[12]")

        assert sad_coverage.text == "N/A"
        
        # Row 6
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 7
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 8
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert start.text == "2021-02-22T16:23:16.158836"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[10]")

        assert stop.text == "2021-02-22T16:24:11.642258"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[11]")

        assert duration.text == "0.925"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[12]")

        assert sad_coverage.text == "N/A"

         # Row 9
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[12]")

        assert sad_coverage.text == "N/A"

        # Row 10
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[12]")

        assert sad_coverage.text == "N/A"

         # Row 11
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[12]")

        assert sad_coverage.text == "N/A"

         # Row 12
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2B"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert downlink_orbit.text == "20717.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert station.text == "SGS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert sensing_orbit.text == "20715"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert datastrip_status.text == "MISSING_SAD"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert start.text == "2021-02-22T16:43:54.133697"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[10]")

        assert stop.text == "2021-02-22T16:45:08.443523"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[11]")

        assert duration.text == "1.238"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[12]")

        assert sad_coverage.text == "N/A"

    def test_processing_dpc_L0_with_plan_but_no_imaging(self):

        filename = "S2A_NPPF_NO_IMAGING.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_REP_PASS_NO_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_OPDPC_L0U_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0
