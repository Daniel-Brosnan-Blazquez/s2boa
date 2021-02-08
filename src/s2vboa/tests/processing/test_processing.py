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
    
    def test_processing_dpc_L0_L1B_L1C_L2A_with_plan_and_rep_pass(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_REP_PASS_NO_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L0U_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L0_L1B.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L1B_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L1C_L2A.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L0U_L0_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L0_L1B_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L1B_L1C_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]
        
        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/processing")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "16077", stop_orbit = "16079", map = True, timeline = True)

        # Check summary pies
        # L0
        processing_data_l0_pie_info = [2,0]

        returned_processing_data_l0_pie_info = self.driver.execute_script('return processing_data_l0;')
        assert processing_data_l0_pie_info == returned_processing_data_l0_pie_info

        # L1B
        processing_data_l1b_pie_info = [2,0]

        returned_processing_data_l1b_pie_info = self.driver.execute_script('return processing_data_l1b;')
        assert processing_data_l1b_pie_info == returned_processing_data_l1b_pie_info

        # L1C
        processing_data_l1c_pie_info = [2,0]

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

        assert expected.text == "2"

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

        assert expected.text == "2"

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

        assert expected.text == "2"

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
        sad_data = self.query_eboa.get_events(gauge_names ={"filter": "SAD_DATA", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-20T22:00:21.024658", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T10:37:11.024915", "op": "=="}])
        isp_valididty = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:29.993268", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:18.226646", "op": "=="}])
        # L0
        isp_valididty_processing_completeness_l0_1 = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0_CHANNEL_1", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:54:07", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T09:06:46", "op": "=="}])
        isp_valididty_processing_completeness_l0_2 = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0_CHANNEL_1", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:29", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:07", "op": "=="}])
        
        map_l0_complete_tooltip_info = [
            {
                "geometries": [
                        isp_valididty_processing_completeness_l0_1[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_valididty_processing_completeness_l0_1[0].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l0_1[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l0_1[0].event_uuid) + "'>S2A_OPER_MSI_L0__DS_SGS__20180721T121507_S20180721T085407_N02.06</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            },
            {
                "geometries": [
                        isp_valididty_processing_completeness_l0_2[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_valididty_processing_completeness_l0_2[0].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l0_2[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l0_2[0].event_uuid) + "'>S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            }, 
        ]

        returned_processing_geometries_complete_l0 = self.driver.execute_script('return processing_geometries_complete_l0;')
        assert map_l0_complete_tooltip_info == returned_processing_geometries_complete_l0

        # L1B
        isp_valididty_processing_completeness_l1b_1 = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1B_CHANNEL_1", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:31", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:09", "op": "=="}])
        isp_valididty_processing_completeness_l1b_2 = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1B_CHANNEL_1", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:54:09", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T09:06:41", "op": "=="}])
        
        map_l1b_complete_tooltip_info = [
            {
                "geometries": [
                        isp_valididty_processing_completeness_l1b_1[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_valididty_processing_completeness_l1b_1[0].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l1b_1[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l1b_1[0].event_uuid) + "'>S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            }, 
            {
                "geometries": [
                        isp_valididty_processing_completeness_l1b_2[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_valididty_processing_completeness_l1b_2[0].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l1b_2[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l1b_2[0].event_uuid) + "'>S2A_OPER_MSI_L1B_DS_SGS__20180721T123126_S20180721T085407_N02.06</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_complete_l1b = self.driver.execute_script('return processing_geometries_complete_l1b;')
        assert map_l1b_complete_tooltip_info == returned_processing_geometries_complete_l1b

        # L1C
        isp_valididty_processing_completeness_l1c_1 = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1C_CHANNEL_1", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:54:09", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T09:06:41", "op": "=="}])
        isp_valididty_processing_completeness_l1c_2 = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1C_CHANNEL_1", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:31", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:09", "op": "=="}])
        
        map_l1c_complete_tooltip_info = [
            {
                "geometries": [
                        isp_valididty_processing_completeness_l1c_1[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_valididty_processing_completeness_l1c_1[0].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l1c_1[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l1c_1[0].event_uuid) + "'>S2A_OPER_MSI_L1C_DS_SGS__20180721T123126_S20180721T085407_N02.06</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            }, 
            {
                "geometries": [
                        isp_valididty_processing_completeness_l1c_2[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_valididty_processing_completeness_l1c_2[0].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l1c_2[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l1c_2[0].event_uuid) + "'>S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            },
        ]

        returned_processing_geometries_complete_l1c = self.driver.execute_script('return processing_geometries_complete_l1c;')
        assert map_l1c_complete_tooltip_info == returned_processing_geometries_complete_l1c

        # L2A
        isp_valididty_processing_completeness_l2a = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L2A_CHANNEL_1", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:31", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])
        
        map_l2a_complete_tooltip_info = [
            {
                "geometries": [
                        isp_valididty_processing_completeness_l2a[0].eventGeometries[0].to_wkt()
                ],
                "id": str(isp_valididty_processing_completeness_l2a[0].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l2a[0].event_uuid) + "'>S2A_OPER_MSI_L2A_DS_MPS__20180721T110122_S20180721T085229_N02.08</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            }, 
        ]

        returned_processing_geometries_complete_l2a = self.driver.execute_script('return processing_geometries_complete_l2a;')
        assert map_l2a_complete_tooltip_info == returned_processing_geometries_complete_l2a

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
                "group": "S2A",
                "id": str(isp_valididty_processing_completeness_l1b_1[0].event_uuid),
                "start": "2018-07-21T08:52:31",
                "stop": "2018-07-21T08:54:09",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l1b_1[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l1b_1[0].event_uuid) + "'>S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-green",
                "group": "S2A",
                "id": str(isp_valididty_processing_completeness_l1b_2[0].event_uuid),
                "start": "2018-07-21T08:54:09",
                "stop": "2018-07-21T09:06:41",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l1b_2[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l1b_2[0].event_uuid) + "'>S2A_OPER_MSI_L1B_DS_SGS__20180721T123126_S20180721T085407_N02.06</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-green",
                "group": "S2A",
                "id": str(isp_valididty_processing_completeness_l1c_1[0].event_uuid),
                "start": "2018-07-21T08:54:09",
                "stop": "2018-07-21T09:06:41",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l1c_1[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l1c_1[0].event_uuid) + "'>S2A_OPER_MSI_L1C_DS_SGS__20180721T123126_S20180721T085407_N02.06</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-green",
                "group": "S2A",
                "id": str(isp_valididty_processing_completeness_l1c_2[0].event_uuid),
                "start": "2018-07-21T08:52:31",
                "stop": "2018-07-21T08:54:09",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l1c_2[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l1c_2[0].event_uuid) + "'>S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-green",
                "group": "S2A",
                "id": str(isp_valididty_processing_completeness_l2a[0].event_uuid),
                "start": "2018-07-21T08:52:31",
                "stop": "2018-07-21T08:54:14",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l2a[0].event_uuid) + "'>S2A_OPER_MSI_L2A_DS_MPS__20180721T110122_S20180721T085229_N02.08</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-green",
                "group": "S2A",
                "id": str(isp_valididty_processing_completeness_l0_1[0].event_uuid),
                "start": "2018-07-21T08:54:07",
                "stop": "2018-07-21T09:06:46",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l0_1[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l0_1[0].event_uuid) + "'>S2A_OPER_MSI_L0__DS_SGS__20180721T121507_S20180721T085407_N02.06</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            },
            {
                "className": "fill-border-green",
                "group": "S2A",
                "id": str(isp_valididty_processing_completeness_l0_2[0].event_uuid),
                "start": "2018-07-21T08:52:29",
                "stop": "2018-07-21T08:54:07",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l0_2[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(isp_valididty_processing_completeness_l0_2[0].event_uuid) + "'>S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Start</td><td>" + isp_valididty[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + isp_valididty[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>SAD coverage</td><td><a href='/eboa_nav/query-event-links/" + str(sad_data[0].event_uuid) + "'>2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>" +
                "</table>"
            },     
        ]

        returned_complete_processing_timeline = self.driver.execute_script('return complete_processing_timeline;')
        assert complete_timeline_tooltip_info == returned_complete_processing_timeline

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

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        start = completeness_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

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

        assert datastrip.text == "S2A_OPER_MSI_L1B_DS_SGS__20180721T123126_S20180721T085407_N02.06"

        start = completeness_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

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

        assert datastrip.text == "S2A_OPER_MSI_L1C_DS_SGS__20180721T123126_S20180721T085407_N02.06"

        start = completeness_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

        # Row 4
        satellite = completeness_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "MPS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        start = completeness_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

        # Row 5
        satellite = completeness_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "MPS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L2A_DS_MPS__20180721T110122_S20180721T085229_N02.08"

        start = completeness_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

        # Row 6
        satellite = completeness_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "MPS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L0__DS_SGS__20180721T121507_S20180721T085407_N02.06"

        start = completeness_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

        # Row 7
        satellite = completeness_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "MPS_"

        level = completeness_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06"

        start = completeness_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

        # Datastrip by UUID completeness table
        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/specific-processing/" + str(isp_valididty[0].event_uuid))

        completeness_datastrip_table = self.driver.find_element_by_id("processing-completeness-table")

        # Row 1
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "MPS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

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

        assert datastrip.text == "S2A_OPER_MSI_L1B_DS_SGS__20180721T123126_S20180721T085407_N02.06"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

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

        assert datastrip.text == "S2A_OPER_MSI_L1C_DS_SGS__20180721T123126_S20180721T085407_N02.06"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

        # Row 4
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "MPS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

        # Row 5
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "MPS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L2A_DS_MPS__20180721T110122_S20180721T085229_N02.08"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

        # Row 6
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "MPS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L0__DS_SGS__20180721T121507_S20180721T085407_N02.06"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

        # Row 7
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2A"

        downlink_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert downlink_orbit.text == "16078.0"

        station = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "MPS_"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert datastrip.text == "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert start.text == "2018-07-21T08:52:29.993268"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert stop.text == "2018-07-21T08:54:18.226646"

        sad_coverage = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert sad_coverage.text == "2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915"

        