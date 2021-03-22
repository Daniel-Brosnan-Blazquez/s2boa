"""
Automated tests for the datatake completeness view

Written by DEIMOS Space S.L. (jubv)

module vboa
"""
import os
import sys
import unittest
import time
import subprocess
import datetime
import s2vboa.tests.datatake_completeness.aux_functions as functions
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


class TestDatatakeCompletenessView(unittest.TestCase):
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

    def test_datatake_completeness_no_data(self):

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/datatake-completeness")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "16077", stop_orbit = "16079", map = True, timeline = True)

        # Check header generated
        header_no_data = wait.until(EC.visibility_of_element_located((By.ID,"header-no-data")))

        assert header_no_data

        table_details_no_data = wait.until(EC.visibility_of_element_located((By.ID,"no-datatake-completeness-data")))

        assert table_details_no_data
    
    def test_datatake_completeness_only_nppf_and_orbpre(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0
        
        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/datatake-completeness")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "16077", stop_orbit = "16079", map = True, timeline = True)

        # Check summary pies
        # L0
        processing_data_l0_pie_info = [0,32.699]

        returned_processing_data_l0_pie_info = self.driver.execute_script('return processing_data_l0;')
        assert processing_data_l0_pie_info == returned_processing_data_l0_pie_info

        # L1B
        processing_data_l1b_pie_info = [0,32.699]

        returned_processing_data_l1b_pie_info = self.driver.execute_script('return processing_data_l1b;')
        assert processing_data_l1b_pie_info == returned_processing_data_l1b_pie_info

        # L1C
        processing_data_l1c_pie_info = [0,32.699]

        returned_processing_data_l1c_pie_info = self.driver.execute_script('return processing_data_l1c;')
        assert processing_data_l1c_pie_info == returned_processing_data_l1c_pie_info
        
        # L2A
        processing_data_l2a_pie_info = [0,32.699]

        returned_processing_data_l2a_pie_info = self.driver.execute_script('return processing_data_l2a;')
        assert processing_data_l2a_pie_info == returned_processing_data_l2a_pie_info
        
        # Check summary expected datatakes
        summary_expected_datatakes = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-datatakes")))

        assert summary_expected_datatakes

        assert summary_expected_datatakes.text == "1"

        # Check summary expected MSI duration for L0
        summary_expected_msi_duration_l0 = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-l0")))

        assert summary_expected_msi_duration_l0

        assert summary_expected_msi_duration_l0.text == "32.699"

        # Check summary expected MSI duration for L1B
        summary_expected_msi_duration_l1b = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-l1b")))

        assert summary_expected_msi_duration_l1b

        assert summary_expected_msi_duration_l1b.text == "32.699"

        # Check summary expected MSI duration for L1C
        summary_expected_msi_duration_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-l1c")))

        assert summary_expected_msi_duration_l1c

        assert summary_expected_msi_duration_l1c.text == "32.699"

        # Check summary expected MSI duration for L2A
        summary_expected_msi_duration_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-l2a")))

        assert summary_expected_msi_duration_l2a

        assert summary_expected_msi_duration_l2a.text == "32.699"

        # Check summary missing MSI duration for L0
        summary_missing_msi_duration_l0 = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-missing-l0")))

        assert summary_missing_msi_duration_l0

        assert summary_missing_msi_duration_l0.text == "32.699"

        # Check summary missing MSI duration for L1B
        summary_missing_msi_duration_l1b = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-missing-l1b")))

        assert summary_missing_msi_duration_l1b

        assert summary_missing_msi_duration_l1b.text == "32.699"

        # Check summary missing MSI duration for L1C
        summary_missing_msi_duration_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-missing-l1c")))

        assert summary_missing_msi_duration_l1c

        assert summary_missing_msi_duration_l1c.text == "32.699"

        # Check summary missing MSI duration for L2A
        summary_missing_msi_duration_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-missing-l2a")))

        assert summary_missing_msi_duration_l2a

        assert summary_missing_msi_duration_l2a.text == "32.699"

        # Check summary datatake completeness table
        summary_table = self.driver.find_element_by_id("summary-datatake-completeness-table")

        # Row 1
        level = summary_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L0"

        expected = summary_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert expected.text == "32.699"

        missing = summary_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert missing.text == "32.699"

        performance = summary_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert performance.text == "0.0"

        # Row 2
        level = summary_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1B"

        expected = summary_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert expected.text == "32.699"

        missing = summary_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert missing.text == "32.699"

        performance = summary_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert performance.text == "0.0"

        # Row 3
        level = summary_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L1C"

        expected = summary_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert expected.text == "32.699"

        missing = summary_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert missing.text == "32.699"

        performance = summary_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert performance.text == "0.0"

        # Row 4
        level = summary_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert level.text == "L2A"

        expected = summary_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert expected.text == "32.699"

        missing = summary_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert missing.text == "32.699"

        performance = summary_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert performance.text == "0.0"

        # Check whether the maps are displayed
        map_section = self.driver.find_element_by_id("datatake-completeness-on-map-section")

        condition = map_section.is_displayed()

        assert condition is True
        
        # Check map complete segments tooltip
        planned_cut_imaging = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_CUT_IMAGING", "op":"=="},
                                                                start_filters =[{"date": "2018-07-21T08:35:53.003000", "op":"=="}],
                                                                stop_filters = [{"date": "2018-07-21T09:08:54.964000", "op": "=="}])
        
        # L0
        planned_imaging_processing_completeness_l0 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op":"=="})
        
        map_l0_missing_tooltip_info = [
            {
                "geometries": [
                        planned_imaging_processing_completeness_l0[0].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l0[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l0[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>32.699</td></tr>"
                "</table>"
            },
        ]

        returned_datatake_completeness_geometries_l0 = self.driver.execute_script('return datatake_completeness_geometries_l0;') 
        functions_vboa.verify_js_var(returned_datatake_completeness_geometries_l0, map_l0_missing_tooltip_info)

        # L1B
        planned_imaging_processing_completeness_l1b = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B", "op":"=="})
        
        map_l1b_missing_tooltip_info = [
            {
                "geometries": [
                        planned_imaging_processing_completeness_l1b[0].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l1b[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1b[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>32.699</td></tr>"
                "</table>"
            },
        ]

        returned_datatake_completeness_geometries_l1b = self.driver.execute_script('return datatake_completeness_geometries_l1b;') 
        functions_vboa.verify_js_var(returned_datatake_completeness_geometries_l1b, map_l1b_missing_tooltip_info)

        # L1C
        planned_imaging_processing_completeness_l1c = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op":"=="})
        
        map_l1c_missing_tooltip_info = [
            {
                "geometries": [
                        planned_imaging_processing_completeness_l1c[0].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l1c[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1c[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>32.699</td></tr>"
                "</table>"
            },
        ]

        returned_datatake_completeness_geometries_l1c = self.driver.execute_script('return datatake_completeness_geometries_l1c;') 
        functions_vboa.verify_js_var(returned_datatake_completeness_geometries_l1c, map_l1c_missing_tooltip_info)

        # L2A
        planned_imaging_processing_completeness_l2a = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L2A", "op":"=="})
        
        map_l2a_missing_tooltip_info = [
            {
                "geometries": [
                        planned_imaging_processing_completeness_l2a[0].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l2a[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l2a[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>32.699</td></tr>"
                "</table>"
            },
        ]

        returned_datatake_completeness_geometries_l2a = self.driver.execute_script('return datatake_completeness_geometries_l2a;') 
        functions_vboa.verify_js_var(returned_datatake_completeness_geometries_l2a, map_l2a_missing_tooltip_info)

        # Check whether the timeline is displayed
        timeline_section = self.driver.find_element_by_id("datatake-completeness-timeline-section")

        condition = timeline_section.is_displayed()
        assert condition is True

        # Check timeline segments tooltip

        timeline_tooltip_info = [
            {
                "className": "fill-border-red",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l0[0].event_uuid),
                "start": "2018-07-21T08:36:08.255634",
                "stop": "2018-07-21T09:08:50.195941",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l0[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>32.699</td></tr>"
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l1b[0].event_uuid),
                "start": "2018-07-21T08:36:08.255634",
                "stop": "2018-07-21T09:08:50.195941",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1b[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>32.699</td></tr>"
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l1c[0].event_uuid),
                "start": "2018-07-21T08:36:08.255634",
                "stop": "2018-07-21T09:08:50.195941",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1c[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>32.699</td></tr>"
                "</table>"
            },     
            {
                "className": "fill-border-red",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l2a[0].event_uuid),
                "start": "2018-07-21T08:36:08.255634",
                "stop": "2018-07-21T09:08:50.195941",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l2a[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>32.699</td></tr>"
                "</table>"
            },
        ]

        returned_datatake_completeness_timeline = self.driver.execute_script('return datatake_completeness_timeline;')
        functions_vboa.verify_js_var(returned_datatake_completeness_timeline, timeline_tooltip_info)

        # Check datatake completeness missing table
        missing_table = self.driver.find_element_by_id("datatake-completeness-missing-table")

        # Row 1
        satellite = missing_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        level = missing_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert level.text == "L0"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        # Row 2
        satellite = missing_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        level = missing_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        # Row 3
        satellite = missing_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        level = missing_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        # Row 4
        satellite = missing_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        level = missing_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"
        
        # Check processing completeness table
        completeness_table = self.driver.find_element_by_id("datatake-completeness-completeness-table")

        # Row 1
        satellite = completeness_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        # Row 2
        satellite = completeness_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        # Row 3
        satellite = completeness_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        # Row 4
        satellite = completeness_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        # Datastrip by UUID missing table
        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid))

        missing_datastrip_table = self.driver.find_element_by_id("datatake-completeness-missing-table")

        # Row 1
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert level.text == "L0"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        # Row 2
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        # Row 3
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        # Row 4
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"
        
        # Datastrip by UUID completeness table
        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid))

        completeness_datastrip_table = self.driver.find_element_by_id("datatake-completeness-completeness-table")

        # Row 1
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        # Row 2
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        # Row 3
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        # Row 4
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

    
    def test_datatake_completeness_dpc_L0_L1B_L1C_L2A_with_plan(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

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

        self.driver.get("http://localhost:5000/views/datatake-completeness")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "16077", stop_orbit = "16079", map = True, timeline = True)

        # Check summary pies
        # L0
        processing_data_l0_pie_info = [1.833,30.866]

        returned_processing_data_l0_pie_info = self.driver.execute_script('return processing_data_l0;')
        assert processing_data_l0_pie_info == returned_processing_data_l0_pie_info

        # L1B
        processing_data_l1b_pie_info = [1.717,30.982]

        returned_processing_data_l1b_pie_info = self.driver.execute_script('return processing_data_l1b;')
        assert processing_data_l1b_pie_info == returned_processing_data_l1b_pie_info

        # L1C
        processing_data_l1c_pie_info = [1.717,30.982]

        returned_processing_data_l1c_pie_info = self.driver.execute_script('return processing_data_l1c;')
        assert processing_data_l1c_pie_info == returned_processing_data_l1c_pie_info
        
        # L2A
        processing_data_l2a_pie_info = [1.717,30.982]

        returned_processing_data_l2a_pie_info = self.driver.execute_script('return processing_data_l2a;')
        assert processing_data_l2a_pie_info == returned_processing_data_l2a_pie_info
        
        # Check summary expected datatakes
        summary_expected_datatakes = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-datatakes")))

        assert summary_expected_datatakes

        assert summary_expected_datatakes.text == "1"

        # Check summary expected MSI duration for L0
        summary_expected_msi_duration_l0 = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-l0")))

        assert summary_expected_msi_duration_l0

        assert summary_expected_msi_duration_l0.text == "32.699"

        # Check summary expected MSI duration for L1B
        summary_expected_msi_duration_l1b = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-l1b")))

        assert summary_expected_msi_duration_l1b

        assert summary_expected_msi_duration_l1b.text == "32.699"

        # Check summary expected MSI duration for L1C
        summary_expected_msi_duration_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-l1c")))

        assert summary_expected_msi_duration_l1c

        assert summary_expected_msi_duration_l1c.text == "32.699"

        # Check summary expected MSI duration for L2A
        summary_expected_msi_duration_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-l2a")))

        assert summary_expected_msi_duration_l2a

        assert summary_expected_msi_duration_l2a.text == "32.699"

        # Check summary missing MSI duration for L0
        summary_missing_msi_duration_l0 = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-missing-l0")))

        assert summary_missing_msi_duration_l0

        assert summary_missing_msi_duration_l0.text == "30.866"

        # Check summary missing MSI duration for L1B
        summary_missing_msi_duration_l1b = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-missing-l1b")))

        assert summary_missing_msi_duration_l1b

        assert summary_missing_msi_duration_l1b.text == "30.982"

        # Check summary missing MSI duration for L1C
        summary_missing_msi_duration_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-missing-l1c")))

        assert summary_missing_msi_duration_l1c

        assert summary_missing_msi_duration_l1c.text == "30.982"

        # Check summary missing MSI duration for L2A
        summary_missing_msi_duration_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-missing-l2a")))

        assert summary_missing_msi_duration_l2a

        assert summary_missing_msi_duration_l2a.text == "30.982"

        # Check summary datatake completeness table
        summary_table = self.driver.find_element_by_id("summary-datatake-completeness-table")

        # Row 1
        level = summary_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L0"

        expected = summary_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert expected.text == "32.699"

        missing = summary_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert missing.text == "30.866"

        performance = summary_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert performance.text == "5.607"

        # Row 2
        level = summary_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1B"

        expected = summary_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert expected.text == "32.699"

        missing = summary_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert missing.text == "30.982"

        performance = summary_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert performance.text == "5.25"

        # Row 3
        level = summary_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L1C"

        expected = summary_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert expected.text == "32.699"

        missing = summary_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert missing.text == "30.982"

        performance = summary_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert performance.text == "5.25"

        # Row 4
        level = summary_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert level.text == "L2A"

        expected = summary_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert expected.text == "32.699"

        missing = summary_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert missing.text == "30.982"

        performance = summary_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert performance.text == "5.25"

        # Check whether the maps are displayed
        map_section = self.driver.find_element_by_id("datatake-completeness-on-map-section")

        condition = map_section.is_displayed()

        assert condition is True
        
        # Check map complete segments tooltip
        planned_cut_imaging = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_CUT_IMAGING", "op":"=="},
                                                                start_filters =[{"date": "2018-07-21T08:35:53.003000", "op":"=="}],
                                                                stop_filters = [{"date": "2018-07-21T09:08:54.964000", "op": "=="}])
        
        # L0
        planned_imaging_processing_completeness_l0 = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op":"=="},
                                                                                order_by = {"field": "start", "descending": False})
        
        map_l0_tooltip_info = [
            {
                "geometries": [
                        planned_imaging_processing_completeness_l0[0].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l0[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l0[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>16.346</td></tr>"
                "</table>"
            },
            {
                "geometries": [
                        planned_imaging_processing_completeness_l0[2].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l0[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l0[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l0[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l0[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l0[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>14.52</td></tr>"
                "</table>"
            },
            {
                "geometries": [
                        planned_imaging_processing_completeness_l0[1].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l0[1].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l0[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l0[1].event_uuid) + "'>S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l0[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l0[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.833</td></tr>"
                "</table>"
            },
        ]

        returned_datatake_completeness_geometries_l0 = self.driver.execute_script('return datatake_completeness_geometries_l0;') 
        functions_vboa.verify_js_var(returned_datatake_completeness_geometries_l0, map_l0_tooltip_info)

        # L1B
        planned_imaging_processing_completeness_l1b = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B", "op":"=="},
                                                                                order_by = {"field": "start", "descending": False})
        
        map_l1b_tooltip_info = [
            {
                "geometries": [
                        planned_imaging_processing_completeness_l1b[0].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l1b[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1b[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>16.379</td></tr>"
                "</table>"
            },
            {
                "geometries": [
                        planned_imaging_processing_completeness_l1b[2].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l1b[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1b[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1b[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1b[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1b[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>14.603</td></tr>"
                "</table>"
            },
            {
                "geometries": [
                        planned_imaging_processing_completeness_l1b[1].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l1b[1].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1b[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1b[1].event_uuid) + "'>S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1b[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1b[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.717</td></tr>"
                "</table>"
            },
        ]

        returned_datatake_completeness_geometries_l1b = self.driver.execute_script('return datatake_completeness_geometries_l1b;') 
        functions_vboa.verify_js_var(returned_datatake_completeness_geometries_l1b, map_l1b_tooltip_info)

        # L1C
        planned_imaging_processing_completeness_l1c = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op":"=="},
                                                                                order_by = {"field": "start", "descending": False})
        
        map_l1c_tooltip_info = [
            {
                "geometries": [
                        planned_imaging_processing_completeness_l1c[0].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l1c[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1c[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>16.379</td></tr>"
                "</table>"
            },
            {
                "geometries": [
                        planned_imaging_processing_completeness_l1c[2].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l1c[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1c[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1c[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1c[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1c[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>14.603</td></tr>"
                "</table>"
            },
            {
                "geometries": [
                        planned_imaging_processing_completeness_l1c[1].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l1c[1].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1c[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1c[1].event_uuid) + "'>S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1c[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1c[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.717</td></tr>"
                "</table>"
            },
        ]

        returned_datatake_completeness_geometries_l1c = self.driver.execute_script('return datatake_completeness_geometries_l1c;') 
        functions_vboa.verify_js_var(returned_datatake_completeness_geometries_l1c, map_l1c_tooltip_info)

        # L2A
        planned_imaging_processing_completeness_l2a = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L2A", "op":"=="},
                                                                                order_by = {"field": "start", "descending": False})
        
        map_l2a_tooltip_info = [
            {
                "geometries": [
                        planned_imaging_processing_completeness_l2a[0].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l2a[0].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l2a[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>16.379</td></tr>"
                "</table>"
            },
            {
                "geometries": [
                        planned_imaging_processing_completeness_l2a[2].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l2a[2].event_uuid),
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l2a[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l2a[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l2a[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l2a[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>14.603</td></tr>"
                "</table>"
            },
            {
                "geometries": [
                        planned_imaging_processing_completeness_l2a[1].eventGeometries[0].to_wkt()
                ],
                "id": str(planned_imaging_processing_completeness_l2a[1].event_uuid),
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                },
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l2a[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l2a[1].event_uuid) + "'>S2A_OPER_MSI_L2A_DS_MPS__20180721T110122_S20180721T085229_N02.08</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l2a[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l2a[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.717</td></tr>"
                "</table>"
            },
        ]

        returned_datatake_completeness_geometries_l2a = self.driver.execute_script('return datatake_completeness_geometries_l2a;') 
        functions_vboa.verify_js_var(returned_datatake_completeness_geometries_l2a, map_l2a_tooltip_info)

        # Check whether the timeline is displayed
        timeline_section = self.driver.find_element_by_id("datatake-completeness-timeline-section")

        condition = timeline_section.is_displayed()
        assert condition is True

        # Check timeline segments tooltip

        timeline_tooltip_info = [
            {
                "className": "fill-border-red",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l0[0].event_uuid),
                "start": "2018-07-21T08:36:08.255634",
                "stop": "2018-07-21T08:52:29",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l0[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l0[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l0[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l0[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>16.346</td></tr>"
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l0[2].event_uuid),
                "start": "2018-07-21T08:54:19",
                "stop": "2018-07-21T09:08:50.195941",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l0[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l0[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l0[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l0[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>14.52</td></tr>"
                "</table>"
            },
            {
                "className": "fill-border-green",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l0[1].event_uuid),
                "start": "2018-07-21T08:52:29",
                "stop": "2018-07-21T08:54:19",
                "timeline": "L0",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l0[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l0[1].event_uuid) + "'>S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l0[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l0[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.833</td></tr>"
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l1b[0].event_uuid),
                "start": "2018-07-21T08:36:08.255634",
                "stop": "2018-07-21T08:52:31",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1b[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1b[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1b[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1b[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>16.379</td></tr>"
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l1b[2].event_uuid),
                "start": "2018-07-21T08:54:14",
                "stop": "2018-07-21T09:08:50.195941",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1b[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1b[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1b[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1b[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>14.603</td></tr>"
                "</table>"
            },
            {
                "className": "fill-border-green",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l1b[1].event_uuid),
                "start": "2018-07-21T08:52:31",
                "stop": "2018-07-21T08:54:14",
                "timeline": "L1B",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1b[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1B</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1b[1].event_uuid) + "'>S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1b[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1b[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.717</td></tr>"
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l1c[0].event_uuid),
                "start": "2018-07-21T08:36:08.255634",
                "stop": "2018-07-21T08:52:31",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1c[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1c[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1c[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1c[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>16.379</td></tr>"
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l1c[2].event_uuid),
                "start": "2018-07-21T08:54:14",
                "stop": "2018-07-21T09:08:50.195941",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1c[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1c[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1c[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1c[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>14.603</td></tr>"
                "</table>"
            },
            {
                "className": "fill-border-green",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l1c[1].event_uuid),
                "start": "2018-07-21T08:52:31",
                "stop": "2018-07-21T08:54:14",
                "timeline": "L1C",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l1c[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L1C</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l1c[1].event_uuid) + "'>S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l1c[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l1c[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.717</td></tr>"
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l2a[0].event_uuid),
                "start": "2018-07-21T08:36:08.255634",
                "stop": "2018-07-21T08:52:31",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l2a[0].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l2a[0].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l2a[0].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>16.379</td></tr>"
                "</table>"
            },
            {
                "className": "fill-border-red",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l2a[2].event_uuid),
                "start": "2018-07-21T08:54:14",
                "stop": "2018-07-21T09:08:50.195941",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l2a[2].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-red>MISSING</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l2a[2].event_uuid) + "'>N/A</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l2a[2].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l2a[2].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>14.603</td></tr>"
                "</table>"
            },
            {
                "className": "fill-border-green",
                "group": "S2A",
                "id": str(planned_imaging_processing_completeness_l2a[1].event_uuid),
                "start": "2018-07-21T08:52:31",
                "stop": "2018-07-21T08:54:14",
                "timeline": "L2A",
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l2a[1].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr>" + 
                "<tr><td>Level</td><td>L2A</td></tr>" +
                "<tr><td>Sensing orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_cut_imaging[0].event_uuid) + "'>16077</a></td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-event-links/" + str(planned_imaging_processing_completeness_l2a[1].event_uuid) + "'>S2A_OPER_MSI_L2A_DS_MPS__20180721T110122_S20180721T085229_N02.08</a></td></tr>" +
                "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                "<tr><td>Start</td><td>" + planned_imaging_processing_completeness_l2a[1].start.isoformat() + "</td></tr>" +
                "<tr><td>Stop</td><td>" + planned_imaging_processing_completeness_l2a[1].stop.isoformat() + "</td></tr>" +
                "<tr><td>Duration (m)</td><td>1.717</td></tr>"
                "</table>"
            },
        ]

        returned_datatake_completeness_timeline = self.driver.execute_script('return datatake_completeness_timeline;')
        functions_vboa.verify_js_var(returned_datatake_completeness_timeline, timeline_tooltip_info)

        # Check datatake completeness missing table
        missing_table = self.driver.find_element_by_id("datatake-completeness-missing-table")

        # Row 1
        satellite = missing_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        level = missing_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert level.text == "L0"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert stop.text == "2018-07-21T08:52:29"

        duration = missing_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert duration.text == "16.346"

        # Row 2
        satellite = missing_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        level = missing_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert stop.text == "2018-07-21T08:52:31"

        duration = missing_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert duration.text == "16.379"

        # Row 3
        satellite = missing_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        level = missing_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert stop.text == "2018-07-21T08:52:31"

        duration = missing_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert duration.text == "16.379"

        # Row 4
        satellite = missing_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        level = missing_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert stop.text == "2018-07-21T08:52:31"

        duration = missing_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert duration.text == "16.379"

        # Row 5
        satellite = missing_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2A"

        level = missing_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert start.text == "2018-07-21T08:54:14"

        stop = missing_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = missing_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert duration.text == "14.603"

        # Row 6
        satellite = missing_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2A"

        level = missing_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert start.text == "2018-07-21T08:54:14"

        stop = missing_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = missing_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert duration.text == "14.603"

        # Row 7
        satellite = missing_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2A"

        level = missing_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert start.text == "2018-07-21T08:54:14"

        stop = missing_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = missing_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert duration.text == "14.603"

        # Row 8
        satellite = missing_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2A"

        level = missing_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert level.text == "L0"

        sensing_orbit = missing_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert start.text == "2018-07-21T08:54:19"

        stop = missing_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = missing_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert duration.text == "14.52"
        
        # Check processing completeness table
        completeness_table = self.driver.find_element_by_id("datatake-completeness-completeness-table")

        # Row 1
        satellite = completeness_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert stop.text == "2018-07-21T08:52:29"

        duration = completeness_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert duration.text == "16.346"

        # Row 2
        satellite = completeness_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert stop.text == "2018-07-21T08:52:31"

        duration = completeness_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert duration.text == "16.379"

        # Row 3
        satellite = completeness_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert stop.text == "2018-07-21T08:52:31"

        duration = completeness_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert duration.text == "16.379"

        # Row 4
        satellite = completeness_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert stop.text == "2018-07-21T08:52:31"

        duration = completeness_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert duration.text == "16.379"

        # Row 5
        satellite = completeness_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert datastrip.text == "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert start.text == "2018-07-21T08:52:29"

        stop = completeness_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert stop.text == "2018-07-21T08:54:19"

        duration = completeness_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert duration.text == "1.833"

        # Row 6
        satellite = completeness_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert datastrip.text == "S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert start.text == "2018-07-21T08:52:31"

        stop = completeness_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert stop.text == "2018-07-21T08:54:14"

        duration = completeness_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert duration.text == "1.717"

        # Row 7
        satellite = completeness_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert datastrip.text == "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert start.text == "2018-07-21T08:52:31"

        stop = completeness_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert stop.text == "2018-07-21T08:54:14"

        duration = completeness_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert duration.text == "1.717"

        # Row 8
        satellite = completeness_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert datastrip.text == "S2A_OPER_MSI_L2A_DS_MPS__20180721T110122_S20180721T085229_N02.08"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert start.text == "2018-07-21T08:52:31"

        stop = completeness_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert stop.text == "2018-07-21T08:54:14"

        duration = completeness_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert duration.text == "1.717"

        # Row 9
        satellite = completeness_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert start.text == "2018-07-21T08:54:14"

        stop = completeness_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = completeness_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert duration.text == "14.603"

        # Row 10
        satellite = completeness_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert start.text == "2018-07-21T08:54:14"

        stop = completeness_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = completeness_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert duration.text == "14.603"

        # Row 11
        satellite = completeness_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert start.text == "2018-07-21T08:54:14"

        stop = completeness_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = completeness_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert duration.text == "14.603"

        # Row 12
        satellite = completeness_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert level.text == "L0"

        sensing_orbit = completeness_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert start.text == "2018-07-21T08:54:19"

        stop = completeness_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"
        
        duration = completeness_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert duration.text == "14.52"

        # Datastrip by UUID
        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/specific-datatake-completeness/" + str(planned_cut_imaging[0].event_uuid))

        # Check summary pies
        # L0
        processing_data_l0_pie_info = [1.833,30.866]

        returned_processing_data_l0_pie_info = self.driver.execute_script('return processing_data_l0;')
        assert processing_data_l0_pie_info == returned_processing_data_l0_pie_info

        # L1B
        processing_data_l1b_pie_info = [1.717,30.982]

        returned_processing_data_l1b_pie_info = self.driver.execute_script('return processing_data_l1b;')
        assert processing_data_l1b_pie_info == returned_processing_data_l1b_pie_info

        # L1C
        processing_data_l1c_pie_info = [1.717,30.982]

        returned_processing_data_l1c_pie_info = self.driver.execute_script('return processing_data_l1c;')
        assert processing_data_l1c_pie_info == returned_processing_data_l1c_pie_info
        
        # L2A
        processing_data_l2a_pie_info = [1.717,30.982]

        returned_processing_data_l2a_pie_info = self.driver.execute_script('return processing_data_l2a;')
        assert processing_data_l2a_pie_info == returned_processing_data_l2a_pie_info
        
        # Check summary expected datatakes
        summary_expected_datatakes = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-datatakes")))

        assert summary_expected_datatakes

        assert summary_expected_datatakes.text == "1"

        # Check summary expected MSI duration for L0
        summary_expected_msi_duration_l0 = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-l0")))

        assert summary_expected_msi_duration_l0

        assert summary_expected_msi_duration_l0.text == "32.699"

        # Check summary expected MSI duration for L1B
        summary_expected_msi_duration_l1b = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-l1b")))

        assert summary_expected_msi_duration_l1b

        assert summary_expected_msi_duration_l1b.text == "32.699"

        # Check summary expected MSI duration for L1C
        summary_expected_msi_duration_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-l1c")))

        assert summary_expected_msi_duration_l1c

        assert summary_expected_msi_duration_l1c.text == "32.699"

        # Check summary expected MSI duration for L2A
        summary_expected_msi_duration_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-l2a")))

        assert summary_expected_msi_duration_l2a

        assert summary_expected_msi_duration_l2a.text == "32.699"

        # Check summary missing MSI duration for L0
        summary_missing_msi_duration_l0 = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-missing-l0")))

        assert summary_missing_msi_duration_l0

        assert summary_missing_msi_duration_l0.text == "30.866"

        # Check summary missing MSI duration for L1B
        summary_missing_msi_duration_l1b = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-missing-l1b")))

        assert summary_missing_msi_duration_l1b

        assert summary_missing_msi_duration_l1b.text == "30.982"

        # Check summary missing MSI duration for L1C
        summary_missing_msi_duration_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-missing-l1c")))

        assert summary_missing_msi_duration_l1c

        assert summary_missing_msi_duration_l1c.text == "30.982"

        # Check summary missing MSI duration for L2A
        summary_missing_msi_duration_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-datatake-completeness-msi-duration-missing-l2a")))

        assert summary_missing_msi_duration_l2a

        assert summary_missing_msi_duration_l2a.text == "30.982"

        # Check summary datatake completeness table
        summary_table = self.driver.find_element_by_id("summary-datatake-completeness-table")

        # Row 1
        level = summary_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L0"

        expected = summary_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert expected.text == "32.699"

        missing = summary_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert missing.text == "30.866"

        performance = summary_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert performance.text == "5.607"

        # Row 2
        level = summary_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1B"

        expected = summary_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert expected.text == "32.699"

        missing = summary_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert missing.text == "30.982"

        performance = summary_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert performance.text == "5.25"

        # Row 3
        level = summary_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L1C"

        expected = summary_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert expected.text == "32.699"

        missing = summary_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert missing.text == "30.982"

        performance = summary_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert performance.text == "5.25"

        # Row 4
        level = summary_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert level.text == "L2A"

        expected = summary_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert expected.text == "32.699"

        missing = summary_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert missing.text == "30.982"

        performance = summary_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert performance.text == "5.25"
        
        # Missing table
        missing_datastrip_table = self.driver.find_element_by_id("datatake-completeness-missing-table")

        # Row 1
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert level.text == "L0"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert stop.text == "2018-07-21T08:52:29"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert duration.text == "16.346"

        # Row 2
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert stop.text == "2018-07-21T08:52:31"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert duration.text == "16.379"

        # Row 3
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert stop.text == "2018-07-21T08:52:31"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert duration.text == "16.379"

        # Row 4
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert stop.text == "2018-07-21T08:52:31"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert duration.text == "16.379"

        # Row 5
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2A"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert start.text == "2018-07-21T08:54:14"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert duration.text == "14.603"

        # Row 6
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2A"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert start.text == "2018-07-21T08:54:14"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert duration.text == "14.603"

        # Row 7
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2A"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert start.text == "2018-07-21T08:54:14"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert duration.text == "14.603"

        # Row 8
        satellite = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2A"

        level = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert level.text == "L0"

        sensing_orbit = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert start.text == "2018-07-21T08:54:19"

        stop = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = missing_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert duration.text == "14.52"
        
        # Completeness table
        completeness_datastrip_table = self.driver.find_element_by_id("datatake-completeness-completeness-table")

        # Row 1
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert stop.text == "2018-07-21T08:52:29"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert duration.text == "16.346"

        # Row 2
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert stop.text == "2018-07-21T08:52:31"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert duration.text == "16.379"

        # Row 3
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert stop.text == "2018-07-21T08:52:31"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert duration.text == "16.379"

        # Row 4
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert start.text == "2018-07-21T08:36:08.255634"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert stop.text == "2018-07-21T08:52:31"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert duration.text == "16.379"

        # Row 5
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert datastrip.text == "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert start.text == "2018-07-21T08:52:29"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert stop.text == "2018-07-21T08:54:19"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert duration.text == "1.833"

        # Row 6
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert datastrip.text == "S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert start.text == "2018-07-21T08:52:31"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert stop.text == "2018-07-21T08:54:14"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert duration.text == "1.717"

        # Row 7
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert datastrip.text == "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert start.text == "2018-07-21T08:52:31"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert stop.text == "2018-07-21T08:54:14"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert duration.text == "1.717"

        # Row 8
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[4]")

        assert datastrip_status.text == "COMPLETE"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[5]")

        assert datastrip.text == "S2A_OPER_MSI_L2A_DS_MPS__20180721T110122_S20180721T085229_N02.08"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[7]")

        assert start.text == "2018-07-21T08:52:31"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[8]")

        assert stop.text == "2018-07-21T08:54:14"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[8]/td[9]")

        assert duration.text == "1.717"

        # Row 9
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[2]")

        assert level.text == "L1B"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[7]")

        assert start.text == "2018-07-21T08:54:14"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[9]/td[9]")

        assert duration.text == "14.603"

        # Row 10
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[2]")

        assert level.text == "L1C"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[7]")

        assert start.text == "2018-07-21T08:54:14"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[10]/td[9]")

        assert duration.text == "14.603"

        # Row 11
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[2]")

        assert level.text == "L2A"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[7]")

        assert start.text == "2018-07-21T08:54:14"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[11]/td[9]")

        assert duration.text == "14.603"

        # Row 12
        satellite = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[1]")

        assert satellite.text == "S2A"

        level = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[2]")

        assert level.text == "L0"

        sensing_orbit = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[3]")

        assert sensing_orbit.text == "16077"

        datastrip_status = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[4]")

        assert datastrip_status.text == "MISSING"

        datastrip = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[5]")

        assert datastrip.text == "N/A"

        imaging_mode = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[6]")

        assert imaging_mode.text == "NOMINAL"

        start = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[7]")

        assert start.text == "2018-07-21T08:54:19"

        stop = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[8]")

        assert stop.text == "2018-07-21T09:08:50.195941"

        duration = completeness_datastrip_table.find_element_by_xpath("tbody/tr[12]/td[9]")

        assert duration.text == "14.52"

        