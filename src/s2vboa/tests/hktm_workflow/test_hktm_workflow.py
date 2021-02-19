"""
Automated tests for the hktm workflow view

Written by DEIMOS Space S.L. (femd)

module vboa
"""
import os
import sys
import unittest
import time
import subprocess
import datetime
import s2vboa.tests.hktm_workflow.aux_functions as functions
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


class TestHktmWorkflowView(unittest.TestCase):
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

    def test_hktm_workflow_no_data(self):

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/hktm-workflow")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "17600", stop_orbit = "17800", timeline = True, table_details = True, evolution = True, map = True)

        # Check section with no data is available
        section_no_data = wait.until(EC.visibility_of_element_located((By.ID,"hktm-workflow-no-expected-hktm")))

        assert section_no_data

        # Check summary expected
        summary_expected = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-expected")))

        assert summary_expected

        assert summary_expected.text == "0"

        # Check summary generated
        summary_generated = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-generated")))

        assert summary_generated

        assert summary_generated.text == "0"
        
        
    def test_hktm_workflow_only_nppf_and_orbpre(self):
        
        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/hktm-workflow")

        functions.query(self.driver, wait, "S2A", start = "2014-07-20T00:00:14", stop = "2020-07-21T23:55:14", start_orbit = "16066", stop_orbit = "16072", timeline = True, table_details = True, evolution = True, map = True)

        # Check summary expected
        summary_expected = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-expected")))

        assert summary_expected

        assert summary_expected.text == "1"

        # Check summary generated
        summary_generated = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-generated")))

        assert summary_generated

        assert summary_generated.text == "0"

        # Check summary missing production
        summary_missing_production = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-missing-production")))

        assert summary_missing_production

        assert summary_missing_production.text == "1"

        # Check summary missing data from PDGS
        summary_missing_data_pdgs = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-missing-data-pdgs")))

        assert summary_missing_data_pdgs

        assert summary_missing_data_pdgs.text == "1"

        # Issues table
        issues_table = self.driver.find_element_by_id("hktm-workflow-issues-hktm-table")

        satellite = issues_table.find_element_by_xpath("tbody/tr[last()]/td[1]")

        assert satellite.text == "S2A"

        orbit = issues_table.find_element_by_xpath("tbody/tr[last()]/td[2]")

        assert orbit.text == "24039"

        station = issues_table.find_element_by_xpath("tbody/tr[last()]/td[3]")

        assert station.text == "N/A"

        anx_time = issues_table.find_element_by_xpath("tbody/tr[last()]/td[4]")

        assert anx_time.text == "2020-01-29T02:57:51.366847"

        status = issues_table.find_element_by_xpath("tbody/tr[last()]/td[5]")

        assert status.text == "PENDING ACQUISITION"

        completeness_status = issues_table.find_element_by_xpath("tbody/tr[last()]/td[6]")

        assert completeness_status.text == "N/A"

        hktm_product = issues_table.find_element_by_xpath("tbody/tr[last()]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = issues_table.find_element_by_xpath("tbody/tr[last()]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = issues_table.find_element_by_xpath("tbody/tr[last()]/td[9]")

        assert time_fos.text == "N/A"

        comments = issues_table.find_element_by_xpath("tbody/tr[last()]/td[10]")

        assert comments.text == ""

        # General table
        general_table = self.driver.find_element_by_id("hktm-workflow-list-hktm-table")

        satellite = general_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        orbit = general_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert orbit.text == "24040"

        station = issues_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "N/A"

        anx_time = general_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert anx_time.text == "2020-01-29T04:38:33.357330"

        status = general_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert status.text == "HKTM PLAYBACK NOT PLANNED"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert completeness_status.text == "HKTM PLAYBACK NOT PLANNED"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert comments.text == ""

        satellite = general_table.find_element_by_xpath("tbody/tr[last()]/td[1]")

        assert satellite.text == "S2A"

        orbit = general_table.find_element_by_xpath("tbody/tr[last()]/td[2]")

        assert orbit.text == "24039"

        station = issues_table.find_element_by_xpath("tbody/tr[last()]/td[3]")

        assert station.text == "N/A"

        anx_time = general_table.find_element_by_xpath("tbody/tr[last()]/td[4]")

        assert anx_time.text == "2020-01-29T02:57:51.366847"

        status = general_table.find_element_by_xpath("tbody/tr[last()]/td[5]")

        assert status.text == "PENDING ACQUISITION"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[last()]/td[6]")

        assert completeness_status.text == "N/A"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[last()]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[last()]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[last()]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[last()]/td[10]")

        assert comments.text == ""
        
    def test_hktm_workflow_only_nppf_and_orbpre_and_rep_pass(self):

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

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/hktm-workflow")

        functions.query(self.driver, wait, "S2A", start = "2014-07-20T00:00:14", stop = "2020-07-21T23:55:14", start_orbit = "16066", stop_orbit = "16072", timeline = True, table_details = True, evolution = True, map = True)

        # Check summary expected
        summary_expected = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-expected")))

        assert summary_expected

        assert summary_expected.text == "1"

        # Check summary generated
        summary_generated = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-generated")))

        assert summary_generated

        assert summary_generated.text == "0"

        # Check summary missing production
        summary_missing_production = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-missing-production")))

        assert summary_missing_production

        assert summary_missing_production.text == "1"

        # Check summary missing production, data received from PDGS
        summary_missing_production_data_received_from_pdgs = wait.until(EC.visibility_of_element_located((By.ID,"summary-missing-hktm-production-data-received")))

        assert summary_missing_production_data_received_from_pdgs

        assert summary_missing_production_data_received_from_pdgs.text == "1"

        # Issues table
        issues_table = self.driver.find_element_by_id("hktm-workflow-issues-hktm-table")

        satellite = issues_table.find_element_by_xpath("tbody/tr[last()]/td[1]")

        assert satellite.text == "S2A"

        orbit = issues_table.find_element_by_xpath("tbody/tr[last()]/td[2]")

        assert orbit.text == "24039"

        station = issues_table.find_element_by_xpath("tbody/tr[last()]/td[3]")

        assert station.text == "N/A"

        anx_time = issues_table.find_element_by_xpath("tbody/tr[last()]/td[4]")

        assert anx_time.text == "2020-01-29T02:57:51.366847"

        status = issues_table.find_element_by_xpath("tbody/tr[last()]/td[5]")

        assert status.text == "MISSING PRODUCTION"

        completeness_status = issues_table.find_element_by_xpath("tbody/tr[last()]/td[6]")

        assert completeness_status.text == "OK"

        hktm_product = issues_table.find_element_by_xpath("tbody/tr[last()]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = issues_table.find_element_by_xpath("tbody/tr[last()]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = issues_table.find_element_by_xpath("tbody/tr[last()]/td[9]")

        assert time_fos.text == "N/A"

        comments = issues_table.find_element_by_xpath("tbody/tr[last()]/td[10]")

        assert comments.text == ""

        # General table
        general_table = self.driver.find_element_by_id("hktm-workflow-list-hktm-table")

        satellite = general_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        orbit = general_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert orbit.text == "24040"

        station = issues_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "N/A"

        anx_time = general_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert anx_time.text == "2020-01-29T04:38:33.357330"

        status = general_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert status.text == "HKTM PLAYBACK NOT PLANNED"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert completeness_status.text == "HKTM PLAYBACK NOT PLANNED"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert comments.text == ""

        satellite = general_table.find_element_by_xpath("tbody/tr[last()]/td[1]")

        assert satellite.text == "S2A"

        orbit = general_table.find_element_by_xpath("tbody/tr[last()]/td[2]")

        assert orbit.text == "24039"

        station = issues_table.find_element_by_xpath("tbody/tr[last()]/td[3]")

        assert station.text == "N/A"

        anx_time = general_table.find_element_by_xpath("tbody/tr[last()]/td[4]")

        assert anx_time.text == "2020-01-29T02:57:51.366847"

        status = general_table.find_element_by_xpath("tbody/tr[last()]/td[5]")

        assert status.text == "MISSING PRODUCTION"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[last()]/td[6]")

        assert completeness_status.text == "OK"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[last()]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[last()]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[last()]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[last()]/td[10]")

        assert comments.text == ""
        
    def test_hktm_workflow(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_MPL_SPSGS__PDMC_20200128T090002_V20200129T000000_20200129T060000.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0
        
        filename = "S2A_REP_PASS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_OPHKTM_VGS2_20200129T034000_V20200129T032508_20200129T032513.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_ophktm.ingestion_ophktm", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0
        
        filename = "S2__REP_OPDC.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dc.ingestion_dc", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/hktm-workflow")

        functions.query(self.driver, wait, "S2A", start = "2014-07-20T00:00:14", stop = "2020-07-21T23:55:14", start_orbit = "16066", stop_orbit = "16072", timeline = True, table_details = True, evolution = True, map = True)

        # Check summary expected
        summary_expected = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-expected")))

        assert summary_expected

        assert summary_expected.text == "1"

        # Check summary generated
        summary_generated = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-generated")))

        assert summary_generated

        assert summary_generated.text == "1"

        # Check number of elements in summary
        assert len(summary_expected.find_elements_by_xpath("../../../div")) == 2

        # General table
        general_table = self.driver.find_element_by_id("hktm-workflow-list-hktm-table")

        satellite = general_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        orbit = general_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert orbit.text == "24040"

        station = general_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "N/A"

        anx_time = general_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert anx_time.text == "2020-01-29T04:38:33.357330"

        status = general_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert status.text == "HKTM PLAYBACK NOT PLANNED"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert completeness_status.text == "HKTM PLAYBACK NOT PLANNED"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert comments.text == ""

        satellite = general_table.find_element_by_xpath("tbody/tr[last()]/td[1]")

        assert satellite.text == "S2A"

        orbit = general_table.find_element_by_xpath("tbody/tr[last()]/td[2]")

        assert orbit.text == "24039"

        station = general_table.find_element_by_xpath("tbody/tr[last()]/td[3]")

        assert station.text == "SGS_"

        anx_time = general_table.find_element_by_xpath("tbody/tr[last()]/td[4]")

        assert anx_time.text == "2020-01-29T02:57:51.366847"

        status = general_table.find_element_by_xpath("tbody/tr[last()]/td[5]")

        assert status.text == "OK"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[last()]/td[6]")

        assert completeness_status.text == "OK"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[last()]/td[7]")

        assert hktm_product.text == "S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[last()]/td[8]")

        assert pdmc_fos_time.text == "2020-01-29T03:29:21"

        time_fos = general_table.find_element_by_xpath("tbody/tr[last()]/td[9]")

        assert time_fos.text == "31.494"

        comments = general_table.find_element_by_xpath("tbody/tr[last()]/td[10]")

        assert comments.text == ""

        planned_playback = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"=="})
        hktm_production_vgs = self.query_eboa.get_events(gauge_names ={"filter": "HKTM_PRODUCTION_VGS", "op":"=="})
        
        # HKTM circulation info
        hktm_circulation_info = [
            {
                "id": str(hktm_production_vgs[0].event_uuid),
                "group": "S2A",
                "x": "2020-01-29T02:57:51.366847",
                "y": "31.494",
                "tooltip": "<table border='1'>" +
                "<tr><td>HKTM Product</td><td><a href='/eboa_nav/query-er/" + str(hktm_production_vgs[0].explicitRef.explicit_ref_uuid) + "'>S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001</a></td></tr>" +
                "<tr><td>Satellite</td><td>S2A</td></tr>" +
                "<tr><td>Orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_playback[0].event_uuid) + "'>24039</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Status</td><td><span class='bold-green'>OK</span></td></tr>" +
                "<tr><td>Completeness status</td><td><span class='bold-green'>OK</span></td></tr>" +
                "<tr><td>ANX time</td><td>2020-01-29T02:57:51.366847</td></tr>" +
                "<tr><td>PDMC-FOS time</td><td>2020-01-29T03:29:21</td></tr>" +
                "<tr><td>Delta to FOS (m)</td><td><span class='bold-green'>31.494</span></td></tr>" +
                "<tr><td>Product size (B)</td><td>38338560.0</td></tr>" +
                "</table>"
            },
        ]
        
        returned_htkm_circulation_info = self.driver.execute_script('return hktm_circulation_events;')
        assert hktm_circulation_info == returned_htkm_circulation_info

        # HKTM size info
        hktm_size_info = [
            {
                "id": str(hktm_production_vgs[0].event_uuid),
                "group": "S2A",
                "x": "2020-01-29T02:57:51.366847",
                "y": "38338560.0",
                "tooltip": "<table border='1'>" +
                "<tr><td>HKTM Product</td><td><a href='/eboa_nav/query-er/" + str(hktm_production_vgs[0].explicitRef.explicit_ref_uuid) + "'>S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001</a></td></tr>" +
                "<tr><td>Satellite</td><td>S2A</td></tr>" +
                "<tr><td>Orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_playback[0].event_uuid) + "'>24039</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Status</td><td><span class='bold-green'>OK</span></td></tr>" +
                "<tr><td>Completeness status</td><td><span class='bold-green'>OK</span></td></tr>" +
                "<tr><td>ANX time</td><td>2020-01-29T02:57:51.366847</td></tr>" +
                "<tr><td>PDMC-FOS time</td><td>2020-01-29T03:29:21</td></tr>" +
                "<tr><td>Delta to FOS (m)</td><td><span class='bold-green'>31.494</span></td></tr>" +
                "<tr><td>Product size (B)</td><td>38338560.0</td></tr>" +
                "</table>"
            },
        ]
        
        returned_htkm_size_info = self.driver.execute_script('return hktm_size_events;')
        assert hktm_size_info == returned_htkm_size_info
        
    def test_hktm_workflow_with_ophktm_and_planning_and_rep_pass(self):

        filename = "S2B_OPER_MPL__NPPF__20201001T120000_20201019T150000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_MPL_ORBPRE_20201015T030112_20201025T030112_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_MPL_SPSGS__PDMC_20201014T090002_V20201015T090000_20201021T090000.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_REP_PASS_E_VGS2_20201015T125515_V20201015T124814_20201015T125511.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_REP_OPHKTM_VGS2_20201015T131302_V20201015T125641_20201015T125641.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_ophktm.ingestion_ophktm", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0


        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/hktm-workflow")

        functions.query(self.driver, wait, "S2B", start = "2020-10-15T00:00:17", stop = "2020-10-15T23:55:17", start_orbit = "18852", stop_orbit = "18858", timeline = True, table_details = True, evolution = True, map = True)

        # Check summary expected
        summary_expected = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-expected")))

        assert summary_expected

        assert summary_expected.text == "3"

        # Check summary generated
        summary_generated = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-generated")))

        assert summary_generated

        assert summary_generated.text == "1"

        # Check summary missing production
        summary_missing_production = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-missing-production")))

        assert summary_missing_production

        assert summary_missing_production.text == "2"

        # Check summary missing circulation
        summary_missing_production = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-missing-circulation")))

        assert summary_missing_production

        assert summary_missing_production.text == "1"

        # Check summary missing data pdgs
        summary_missing_production = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-missing-data-pdgs")))

        assert summary_missing_production

        assert summary_missing_production.text == "2"

        # Check if table with issues appears
        issues_hktm_table = wait.until(EC.visibility_of_element_located((By.ID,"hktm-workflow-issues-hktm-table_wrapper")))

        assert issues_hktm_table
        
        # General table
        general_table = self.driver.find_element_by_id("hktm-workflow-list-hktm-table")

        # Row 1
        satellite = general_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2B"

        orbit = general_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert orbit.text == "18858"

        station = general_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "N/A"

        anx_time = general_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert anx_time.text == "2020-10-15T18:54:40.931594"

        status = general_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert status.text == "HKTM PLAYBACK NOT PLANNED"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert completeness_status.text == "HKTM PLAYBACK NOT PLANNED"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert comments.text == ""

        # Row 2
        satellite = general_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2B"

        orbit = general_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert orbit.text == "18857"

        station = general_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "N/A"

        anx_time = general_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert anx_time.text == "2020-10-15T17:13:58.892870"

        status = general_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert status.text == "HKTM PLAYBACK NOT PLANNED"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert completeness_status.text == "HKTM PLAYBACK NOT PLANNED"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert comments.text == ""

        # Row 3
        satellite = general_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert satellite.text == "S2B"

        orbit = general_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert orbit.text == "18856"

        station = general_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert station.text == "N/A"

        anx_time = general_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert anx_time.text == "2020-10-15T15:33:16.850267"

        status = general_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert status.text == "HKTM PLAYBACK NOT PLANNED"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert completeness_status.text == "HKTM PLAYBACK NOT PLANNED"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert comments.text == ""

        # Row 4
        satellite = general_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2B"

        orbit = general_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert orbit.text == "18855"

        station = general_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "SGS_"

        anx_time = general_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert anx_time.text == "2020-10-15T13:52:34.882710"

        status = general_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert status.text == "PENDING ACQUISITION"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert completeness_status.text == "N/A"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert comments.text == ""

        # Row 5
        satellite = general_table.find_element_by_xpath("tbody/tr[5]/td[1]")

        assert satellite.text == "S2B"

        orbit = general_table.find_element_by_xpath("tbody/tr[5]/td[2]")

        assert orbit.text == "18854"

        station = general_table.find_element_by_xpath("tbody/tr[5]/td[3]")

        assert station.text == "SGS_"

        anx_time = general_table.find_element_by_xpath("tbody/tr[5]/td[4]")

        assert anx_time.text == "2020-10-15T12:11:52.978670"

        status = general_table.find_element_by_xpath("tbody/tr[5]/td[5]")

        assert status.text == "MISSING CIRCULATION TO FOS"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[5]/td[6]")

        assert completeness_status.text == "N/A"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[5]/td[7]")

        assert hktm_product.text == "S2B_OPER_PRD_HKTM___20201015T125434_20201015T125511_0001"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[5]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[5]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[5]/td[10]")

        assert comments.text == ""

        # Row 6
        satellite = general_table.find_element_by_xpath("tbody/tr[6]/td[1]")

        assert satellite.text == "S2B"

        orbit = general_table.find_element_by_xpath("tbody/tr[6]/td[2]")

        assert orbit.text == "18853"

        station = general_table.find_element_by_xpath("tbody/tr[6]/td[3]")

        assert station.text == "SGS_"

        anx_time = general_table.find_element_by_xpath("tbody/tr[6]/td[4]")

        assert anx_time.text == "2020-10-15T10:31:11.089630"

        status = general_table.find_element_by_xpath("tbody/tr[6]/td[5]")

        assert status.text == "PENDING ACQUISITION"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[6]/td[6]")

        assert completeness_status.text == "N/A"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[6]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[6]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[6]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[6]/td[10]")

        assert comments.text == ""

        # Row 7
        satellite = general_table.find_element_by_xpath("tbody/tr[7]/td[1]")

        assert satellite.text == "S2B"

        orbit = general_table.find_element_by_xpath("tbody/tr[7]/td[2]")

        assert orbit.text == "18852"

        station = general_table.find_element_by_xpath("tbody/tr[7]/td[3]")

        assert station.text == "N/A"

        anx_time = general_table.find_element_by_xpath("tbody/tr[7]/td[4]")

        assert anx_time.text == "2020-10-15T08:50:29.168713"

        status = general_table.find_element_by_xpath("tbody/tr[7]/td[5]")

        assert status.text == "HKTM PLAYBACK NOT PLANNED"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[7]/td[6]")

        assert completeness_status.text == "HKTM PLAYBACK NOT PLANNED"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[7]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[7]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[7]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[7]/td[10]")

        assert comments.text == ""

    def test_hktm_workflow_with_missing(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_MPL_SPSGS__PDMC_20200128T090002_V20200129T000000_20200129T060000.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0
        
        filename = "S2A_REP_PASS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_OPHKTM_VGS2_20200129T034000_V20200129T032508_20200129T032513.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_ophktm.ingestion_ophktm", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0
        
        filename = "S2__REP_OPDC.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dc.ingestion_dc", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_NPPF_ONLY_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE_ONLY_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_REP_PASS_ONLY_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/hktm-workflow")

        functions.query(self.driver, wait, "S2A", start = "2014-07-20T00:00:14", stop = "2020-07-21T23:55:14", start_orbit = "16066", stop_orbit = "16072", timeline = True, table_details = True, evolution = True, map = True)

        # Check summary expected
        summary_expected = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-expected")))

        assert summary_expected

        assert summary_expected.text == "2"

        # Check summary generated
        summary_generated = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-generated")))

        assert summary_generated

        assert summary_generated.text == "1"

        # Check summary generated
        summary_missing = wait.until(EC.visibility_of_element_located((By.ID,"summary-hktm-workflow-missing-production")))

        assert summary_missing

        assert summary_missing.text == "1"

        # Check summary generated
        summary_missing_data_received_by_pdgs = wait.until(EC.visibility_of_element_located((By.ID,"summary-missing-hktm-production-data-received")))

        assert summary_missing_data_received_by_pdgs

        assert summary_missing_data_received_by_pdgs.text == "1"

        # Check number of elements in summary
        assert len(summary_expected.find_elements_by_xpath("../../../div")) == 4

        # General table
        general_table = self.driver.find_element_by_id("hktm-workflow-list-hktm-table")

        satellite = general_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert satellite.text == "S2A"

        orbit = general_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert orbit.text == "24040"

        station = general_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert station.text == "N/A"

        anx_time = general_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert anx_time.text == "2020-01-29T04:38:33.357330"

        status = general_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert status.text == "HKTM PLAYBACK NOT PLANNED"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert completeness_status.text == "HKTM PLAYBACK NOT PLANNED"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert comments.text == ""

        satellite = general_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert satellite.text == "S2A"

        orbit = general_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert orbit.text == "24039"

        station = general_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert station.text == "SGS_"

        anx_time = general_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert anx_time.text == "2020-01-29T02:57:51.366847"

        status = general_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert status.text == "OK"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert completeness_status.text == "OK"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert hktm_product.text == "S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert pdmc_fos_time.text == "2020-01-29T03:29:21"

        time_fos = general_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert time_fos.text == "31.494"

        comments = general_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert comments.text == ""

        satellite = general_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert satellite.text == "S2A"

        orbit = general_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert orbit.text == "16073"

        station = general_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert station.text == "N/A"

        anx_time = general_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert anx_time.text == "2018-07-21T01:27:21.897531"

        status = general_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert status.text == "MISSING PRODUCTION"

        completeness_status = general_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert completeness_status.text == "OK"

        hktm_product = general_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert hktm_product.text == "N/A"

        pdmc_fos_time = general_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert pdmc_fos_time.text == "N/A"

        time_fos = general_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert time_fos.text == "N/A"

        comments = general_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert comments.text == ""

        planned_playback = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_PLAYBACK", "op":"=="}, order_by = {"field": "start", "descending": True})
        hktm_production_vgs = self.query_eboa.get_events(gauge_names ={"filter": "HKTM_PRODUCTION_VGS", "op":"=="})
        
        # HKTM circulation info
        hktm_circulation_info = [
            {
                "id": str(hktm_production_vgs[0].event_uuid),
                "group": "S2A",
                "x": "2020-01-29T02:57:51.366847",
                "y": "31.494",
                "tooltip": "<table border='1'>" +
                "<tr><td>HKTM Product</td><td><a href='/eboa_nav/query-er/" + str(hktm_production_vgs[0].explicitRef.explicit_ref_uuid) + "'>S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001</a></td></tr>" +
                "<tr><td>Satellite</td><td>S2A</td></tr>" +
                "<tr><td>Orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_playback[0].event_uuid) + "'>24039</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Status</td><td><span class='bold-green'>OK</span></td></tr>" +
                "<tr><td>Completeness status</td><td><span class='bold-green'>OK</span></td></tr>" +
                "<tr><td>ANX time</td><td>2020-01-29T02:57:51.366847</td></tr>" +
                "<tr><td>PDMC-FOS time</td><td>2020-01-29T03:29:21</td></tr>" +
                "<tr><td>Delta to FOS (m)</td><td><span class='bold-green'>31.494</span></td></tr>" +
                "<tr><td>Product size (B)</td><td>38338560.0</td></tr>" +
                "</table>"
            },
        ]
        
        returned_htkm_circulation_info = self.driver.execute_script('return hktm_circulation_events;')
        assert hktm_circulation_info == returned_htkm_circulation_info

        # HKTM size info
        hktm_size_info = [
            {
                "id": str(hktm_production_vgs[0].event_uuid),
                "group": "S2A",
                "x": "2020-01-29T02:57:51.366847",
                "y": "38338560.0",
                "tooltip": "<table border='1'>" +
                "<tr><td>HKTM Product</td><td><a href='/eboa_nav/query-er/" + str(hktm_production_vgs[0].explicitRef.explicit_ref_uuid) + "'>S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001</a></td></tr>" +
                "<tr><td>Satellite</td><td>S2A</td></tr>" +
                "<tr><td>Orbit</td><td><a href='/eboa_nav/query-event-links/" + str(planned_playback[0].event_uuid) + "'>24039</a></td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Status</td><td><span class='bold-green'>OK</span></td></tr>" +
                "<tr><td>Completeness status</td><td><span class='bold-green'>OK</span></td></tr>" +
                "<tr><td>ANX time</td><td>2020-01-29T02:57:51.366847</td></tr>" +
                "<tr><td>PDMC-FOS time</td><td>2020-01-29T03:29:21</td></tr>" +
                "<tr><td>Delta to FOS (m)</td><td><span class='bold-green'>31.494</span></td></tr>" +
                "<tr><td>Product size (B)</td><td>38338560.0</td></tr>" +
                "</table>"
            },
        ]
        
        returned_htkm_size_info = self.driver.execute_script('return hktm_size_events;')
        assert hktm_size_info == returned_htkm_size_info
