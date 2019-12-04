"""
Automated tests for the planning view

Written by DEIMOS Space S.L. (femd)

module vboa
"""
import os
import sys
import unittest
import time
import subprocess
import datetime
import s2vboa.tests.planning.aux_functions as functions
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


class TestPlanningView(unittest.TestCase):
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

    def test_planning_no_data(self):

        wait = WebDriverWait(self.driver,5);

        self.driver.get("http://localhost:5000/views/planning")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "17600", stop_orbit = "17800", timeline = True, table_details = True, evolution = True, map = True)

        # Check header generated
        header_no_data = wait.until(EC.visibility_of_element_located((By.ID,"header-no-data")))

        assert header_no_data

        summary_no_data = wait.until(EC.visibility_of_element_located((By.ID,"summary-no-imaging")))

        assert summary_no_data

        imaging_no_data = wait.until(EC.visibility_of_element_located((By.ID,"imaging-no-imaging")))

        assert imaging_no_data

        playback_no_data = wait.until(EC.visibility_of_element_located((By.ID,"playback-no-playback")))

        assert playback_no_data

        timeline_no_data = wait.until(EC.visibility_of_element_located((By.ID,"timeline-no-planning")))

        assert timeline_no_data

    def test_planning_only_nppf_and_orbpre(self):
        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        wait = WebDriverWait(self.driver,5);

        self.driver.get("http://localhost:5000/views/planning")

        functions.query(self.driver, wait, "S2A", start = "2018-07-20T00:00:14", stop = "2018-07-21T23:55:14", start_orbit = "16066", stop_orbit = "16072", timeline = True, table_details = True, evolution = True, map = True)

        #Check table no playback exists

        playback_not_covered = self.driver.find_element_by_id("playback-not-covered")

        assert playback_not_covered

        # Not covered details

        not_covered_table = self.driver.find_element_by_id("playback-not-covered-table")

        not_covered_satellite = not_covered_table.find_element_by_xpath("tbody/tr[last()]/td[1]").text

        assert not_covered_satellite == "S2A"

        not_covered_orbit = not_covered_table.find_element_by_xpath("tbody/tr[last()]/td[2]").text

        assert not_covered_orbit == "16066"

        not_covered_start = not_covered_table.find_element_by_xpath("tbody/tr[last()]/td[3]").text

        assert not_covered_start == "2018-07-20T14:02:38.392053"

        not_covered_stop = not_covered_table.find_element_by_xpath("tbody/tr[last()]/td[4]").text

        assert not_covered_stop == "2018-07-20T14:14:20.241401"

        not_covered_duration_s = not_covered_table.find_element_by_xpath("tbody/tr[last()]/td[5]").text

        assert not_covered_duration_s == "701.849"

        not_covered_duration_m = not_covered_table.find_element_by_xpath("tbody/tr[last()]/td[6]").text

        assert not_covered_duration_m == "11.697"

        not_covered_playback_type = not_covered_table.find_element_by_xpath("tbody/tr[last()]/td[7]").text

        assert not_covered_playback_type == "NOMINAL"

        not_covered_parameters = not_covered_table.find_element_by_xpath("tbody/tr[last()]/td[8]").text

        assert not_covered_parameters == "MEM_FREE=1\nSCN_DUP=0\nSCN_RWD=1"

        not_covered_plan_file = not_covered_table.find_element_by_xpath("tbody/tr[last()]/td[9]").text

        assert not_covered_plan_file == "S2A_NPPF.EOF"

        not_covered_uuid = not_covered_table.find_element_by_xpath("tbody/tr[last()]/td[11]").text

        assert re.match("........-....-....-....-............", not_covered_uuid)

        #Not covered number of playbacks

        playbacks_number = len(not_covered_table.find_elements_by_xpath("tbody/tr"))

        assert playbacks_number == 6

    def test_planning_whole(self):
        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_MPL_SPSGS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2_SRA_EDRS_A.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_slot_request_edrs.ingestion_slot_request_edrs", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        wait = WebDriverWait(self.driver,5);

        self.driver.get("http://localhost:5000/views/planning")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "17600", stop_orbit = "17800", timeline = True, table_details = True, evolution = True, map = True)

        # Header
        header_table = self.driver.find_element_by_id("header-table")

        orbit_start = header_table.find_element_by_xpath("tbody/tr[th[text() = 'Orbit information']]/td[1]")

        assert orbit_start.text == "16066"

        orbit_stop = header_table.find_element_by_xpath("tbody/tr[th[text() = 'Orbit information']]/td[2]")

        assert orbit_stop.text == "16072"

        time_start = header_table.find_element_by_xpath("tbody/tr[th[text() = 'Time information']]/td[1]")

        assert time_start.text == "2018-07-01T00:00:00"

        time_stop = header_table.find_element_by_xpath("tbody/tr[th[text() = 'Time information']]/td[2]")

        assert time_stop.text == "2018-07-31T23:59:59"

        #Summary

        ## Definite Mission

        summary_S2A_table = self.driver.find_element_by_id("summary-table-S2A")

        RT_imagings = summary_S2A_table.find_element_by_xpath("tbody/tr[th[text() = 'Percentage of planned RT imagings (%):']]/td[1]")

        assert RT_imagings.text == "0.000"

        NRT_imagings = summary_S2A_table.find_element_by_xpath("tbody/tr[th[text() = 'Percentage of planned NRT imagings (%):']]/td[1]")

        assert NRT_imagings.text == "8.815"

        nominal_imagings = summary_S2A_table.find_element_by_xpath("tbody/tr[th[text() = 'Percentage of planned Nominal imagings (%):']]/td[1]")

        assert nominal_imagings.text == "91.185"

        XBand_playbacks = summary_S2A_table.find_element_by_xpath("tbody/tr[th[text() = 'Percentage of playbacks through the X-Band (%):']]/td[1]")

        assert XBand_playbacks.text == "59.902"

        OCP_playbacks = summary_S2A_table.find_element_by_xpath("tbody/tr[th[text() = 'Percentage of playbacks through the OCP (%):']]/td[1]")

        assert OCP_playbacks.text == "40.098"

        duration_XBand_playbacks = summary_S2A_table.find_element_by_xpath("tbody/tr[th[text() = 'Average duration of playbacks through X-Band (minutes):']]/td[1]")

        assert duration_XBand_playbacks.text == "11.671"

        duration_OCP_playbacks = summary_S2A_table.find_element_by_xpath("tbody/tr[th[text() = 'Average duration of playbacks through OCP (minutes):']]/td[1]")

        assert duration_OCP_playbacks.text == "15.625"

        ## All Missions

        summary_all_missions_table = self.driver.find_element_by_id("summary-table-S2")

        RT_imagings = summary_all_missions_table.find_element_by_xpath("tbody/tr[th[text() = 'Percentage of planned RT imagings (%):']]/td[1]")

        assert RT_imagings.text == "0.000"

        NRT_imagings = summary_all_missions_table.find_element_by_xpath("tbody/tr[th[text() = 'Percentage of planned NRT imagings (%):']]/td[1]")

        assert NRT_imagings.text == "8.815"

        nominal_imagings = summary_all_missions_table.find_element_by_xpath("tbody/tr[th[text() = 'Percentage of planned Nominal imagings (%):']]/td[1]")

        assert nominal_imagings.text == "91.185"

        XBand_playbacks = summary_all_missions_table.find_element_by_xpath("tbody/tr[th[text() = 'Percentage of playbacks through the X-Band (%):']]/td[1]")

        assert XBand_playbacks.text == "59.902"

        OCP_playbacks = summary_all_missions_table.find_element_by_xpath("tbody/tr[th[text() = 'Percentage of playbacks through the OCP (%):']]/td[1]")

        assert OCP_playbacks.text == "40.098"

        duration_XBand_playbacks = summary_all_missions_table.find_element_by_xpath("tbody/tr[th[text() = 'Average duration of playbacks through X-Band (minutes):']]/td[1]")

        assert duration_XBand_playbacks.text == "11.671"

        duration_OCP_playbacks = summary_all_missions_table.find_element_by_xpath("tbody/tr[th[text() = 'Average duration of playbacks through OCP (minutes):']]/td[1]")

        assert duration_OCP_playbacks.text == "15.625"

        # Imaging

        imaging_reporting_orbits = self.driver.find_element_by_id("imaging-reporting-orbits")

        assert imaging_reporting_orbits.text == "Mission S2A: 16066 - 16072 (7)"

        imaging_used_orbits = self.driver.find_element_by_id("imaging-used-orbits")

        assert imaging_used_orbits.text == "Mission S2A: 16066 - 16068 (3)"

        ## Definite Mission

        ### Mode duration

        mode_S2A_duration_table = self.driver.find_element_by_id("imaging-mode-duration-table-S2A")

        duration_nominal = mode_S2A_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'NOMINAL']]/td[2]")

        assert duration_nominal.text == "1.427"

        duration_sun_cal = mode_S2A_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'SUN_CAL']]/td[2]")

        assert duration_sun_cal.text == "6.119"

        duration_dark_cal_csm_open = mode_S2A_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'DARK_CAL_CSM_OPEN']]/td[2]")

        assert duration_dark_cal_csm_open.text == "20.151"

        duration_dark_cal_csm_close = mode_S2A_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'DARK_CAL_CSM_CLOSE']]/td[2]")

        assert duration_dark_cal_csm_close.text == "0.343"

        duration_vicarious_cal = mode_S2A_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'VICARIOUS_CAL']]/td[2]")

        assert duration_vicarious_cal.text == "15.37"

        duration_raw = mode_S2A_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'RAW']]/td[2]")

        assert duration_raw.text == "6.175"

        duration_test = mode_S2A_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'TEST']]/td[2]")

        assert duration_test.text == "19.827"

        ### Total duration

        total_S2A_duration_table = self.driver.find_element_by_id("imaging-total-duration-table-S2A")

        total_duration = total_S2A_duration_table.find_element_by_xpath("tbody/tr[th[text() = 'Total(m):']]/td[1]")

        assert total_duration.text == "69.411"

        total_average = total_S2A_duration_table.find_element_by_xpath("tbody/tr[th[text() = 'Total average(m):']]/td[1]")

        assert total_average.text == "9.916"

        net_average = total_S2A_duration_table.find_element_by_xpath("tbody/tr[th[text() = 'Net average(m):']]/td[1]")

        assert net_average.text == "23.137"

        minimum = total_S2A_duration_table.find_element_by_xpath("tbody/tr[th[text() = 'Minimum(m):']]/td[1]")

        assert minimum.text == "0.343"

        maximum = total_S2A_duration_table.find_element_by_xpath("tbody/tr[th[text() = 'Maximum(m):']]/td[1]")

        assert maximum.text == "20.151"

        ## All Missions

        ### Mode duration

        mode_all_missions_duration_table = self.driver.find_element_by_id("imaging-mode-duration-table-S2A")

        duration_nominal = mode_all_missions_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'NOMINAL']]/td[2]")

        assert duration_nominal.text == "1.427"

        duration_sun_cal = mode_all_missions_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'SUN_CAL']]/td[2]")

        assert duration_sun_cal.text == "6.119"

        duration_dark_cal_csm_open = mode_all_missions_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'DARK_CAL_CSM_OPEN']]/td[2]")

        assert duration_dark_cal_csm_open.text == "20.151"

        duration_dark_cal_csm_close = mode_all_missions_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'DARK_CAL_CSM_CLOSE']]/td[2]")

        assert duration_dark_cal_csm_close.text == "0.343"

        duration_vicarious_cal = mode_all_missions_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'VICARIOUS_CAL']]/td[2]")

        assert duration_vicarious_cal.text == "15.37"

        duration_raw = mode_all_missions_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'RAW']]/td[2]")

        assert duration_raw.text == "6.175"

        duration_test = mode_all_missions_duration_table.find_element_by_xpath("tbody/tr[td[text() = 'TEST']]/td[2]")

        assert duration_test.text == "19.827"

        ### Total duration

        total_all_missions_duration_table = self.driver.find_element_by_id("imaging-total-duration-table-S2A")

        total_duration = total_all_missions_duration_table.find_element_by_xpath("tbody/tr[th[text() = 'Total(m):']]/td[1]")

        assert total_duration.text == "69.411"

        total_average = total_all_missions_duration_table.find_element_by_xpath("tbody/tr[th[text() = 'Total average(m):']]/td[1]")

        assert total_average.text == "9.916"

        net_average = total_all_missions_duration_table.find_element_by_xpath("tbody/tr[th[text() = 'Net average(m):']]/td[1]")

        assert net_average.text == "23.137"

        minimum = total_all_missions_duration_table.find_element_by_xpath("tbody/tr[th[text() = 'Minimum(m):']]/td[1]")

        assert minimum.text == "0.343"

        maximum = total_all_missions_duration_table.find_element_by_xpath("tbody/tr[th[text() = 'Maximum(m):']]/td[1]")

        assert maximum.text == "20.151"

        # Graph duration imagings

        events = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="})

        events.sort(key=lambda x:x.start, reverse=True)

        imaging_xy_events = [
        {
            "id": str(events[0].event_uuid),
            "group": "S2A",
            "x": "2018-07-20 17:28:56.736288",
            "y": "19.826622750000002",
            "tooltip":  "<table border='1'>" +
                        "<tr><td>UUID</td><td>" + str(events[0].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16068</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T17:28:56.736288</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T17:48:46.333653</td></tr>" +
                        "<tr><td>Duration(m)</td><td>19.827</td></tr>" +
                        "<tr><td>Imaging mode</td><td>TEST</td></tr>" +
                        "<tr><td>Record type</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        },
        {
            "id": str(events[1].event_uuid),
            "group": "S2A",
            "x": "2018-07-20 16:05:09.432097",
            "y": "6.175066866666667",
            "tooltip":  "<table border='1'>" +
                        "<tr><td>UUID</td><td>" + str(events[1].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16067</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T16:05:09.432097</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T16:11:19.936109</td></tr>" +
                        "<tr><td>Duration(m)</td><td>6.175</td></tr>" +
                        "<tr><td>Imaging mode</td><td>RAW</td></tr>" +
                        "<tr><td>Record type</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        },
        {
            "id": str(events[2].event_uuid),
            "group": "S2A",
            "x": "2018-07-20 15:49:02.890406",
            "y": "15.369803216666666",
            "tooltip":  "<table border='1'>" +
                        "<tr><td>UUID</td><td>" + str(events[2].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16067</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T15:49:02.890406</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T16:04:25.078599</td></tr>" +
                        "<tr><td>Duration(m)</td><td>15.370</td></tr>" +
                        "<tr><td>Imaging mode</td><td>VICARIOUS_CAL</td></tr>" +
                        "<tr><td>Record type</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(events[2].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        },
        {
            "id": str(events[3].event_uuid),
            "group": "S2A",
            "x": "2018-07-20 15:48:09.150610",
            "y": "0.34286855000000005",
            "tooltip":  "<table border='1'>" +
                        "<tr><td>UUID</td><td>" + str(events[3].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16067</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T15:48:09.150610</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T15:48:29.722723</td></tr>" +
                        "<tr><td>Duration(m)</td><td>0.343</td></tr>" +
                        "<tr><td>Imaging mode</td><td>DARK_CAL_CSM_CLOSE</td></tr>" +
                        "<tr><td>Record type</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(events[3].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        },
        {
            "id": str(events[4].event_uuid),
            "group": "S2A",
            "x": "2018-07-20 14:27:50.784884",
            "y": "20.151175683333335",
            "tooltip":  "<table border='1'>" +
                        "<tr><td>UUID</td><td>" + str(events[4].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16066</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T14:27:50.784884</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T14:47:59.855425</td></tr>" +
                        "<tr><td>Duration(m)</td><td>20.151</td></tr>" +
                        "<tr><td>Imaging mode</td><td>DARK_CAL_CSM_OPEN</td></tr>" +
                        "<tr><td>Record type</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(events[4].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        },
        {
            "id": str(events[5].event_uuid),
            "group": "S2A",
            "x": "2018-07-20 14:10:02.951732",
            "y": "6.118657633333333",
            "tooltip":  "<table border='1'>" +
                        "<tr><td>UUID</td><td>"+ str(events[5].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16066</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T14:10:02.951732</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T14:16:10.071190</td></tr>" +
                        "<tr><td>Duration(m)</td><td>6.119</td></tr>" +
                        "<tr><td>Imaging mode</td><td>SUN_CAL</td></tr>" +
                        "<tr><td>Record type</td><td>NRT</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(events[5].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        },
        {
            "id": str(events[6].event_uuid),
            "group": "S2A",
            "x": "2018-07-20 14:07:32.793311",
            "y": "1.4268956000000002",
            "tooltip":  "<table border='1'>" +
                        "<tr><td>UUID</td><td>" + str(events[6].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16066</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T14:07:32.793311</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T14:08:58.407047</td></tr>" +
                        "<tr><td>Duration(m)</td><td>1.427</td></tr>" +
                        "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Record type</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(events[6].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        }
        ]

        assert self.driver.execute_script('return imaging_xy_events;') == imaging_xy_events

        # Imaging details

        imaging_details_table = self.driver.find_element_by_id("imaging-details-table")

        imaging_details_satellite = imaging_details_table.find_element_by_xpath("tbody/tr[last()]/td[1]").text

        assert imaging_details_satellite == "S2A"

        imaging_details_orbit = imaging_details_table.find_element_by_xpath("tbody/tr[last()]/td[2]").text

        assert imaging_details_orbit == "16066"

        imaging_details_start = imaging_details_table.find_element_by_xpath("tbody/tr[last()]/td[3]").text

        assert imaging_details_start == "2018-07-20T14:07:32.793311"

        imaging_details_stop = imaging_details_table.find_element_by_xpath("tbody/tr[last()]/td[4]").text

        assert imaging_details_stop == "2018-07-20T14:08:58.407047"

        imaging_details_duration_s = imaging_details_table.find_element_by_xpath("tbody/tr[last()]/td[5]").text

        assert imaging_details_duration_s == "85.614"

        imaging_details_duration_m = imaging_details_table.find_element_by_xpath("tbody/tr[last()]/td[6]").text

        assert imaging_details_duration_m == "1.427"

        imaging_details_imaging_mode = imaging_details_table.find_element_by_xpath("tbody/tr[last()]/td[7]").text

        assert imaging_details_imaging_mode == "NOMINAL"

        imaging_details_record_type = imaging_details_table.find_element_by_xpath("tbody/tr[last()]/td[8]").text

        assert imaging_details_record_type == "NOMINAL"

        imaging_details_parameters = imaging_details_table.find_element_by_xpath("tbody/tr[last()]/td[9]").text

        assert imaging_details_parameters == "start_scn_dup=0"

        imaging_details_plan_file = imaging_details_table.find_element_by_xpath("tbody/tr[last()]/td[10]").text

        assert imaging_details_plan_file == "S2A_NPPF.EOF"

        imaging_details_uuid = imaging_details_table.find_element_by_xpath("tbody/tr[last()]/td[12]").text

        assert re.match("........-....-....-....-............", imaging_details_uuid)

        # Playback

        playback_reporting_orbits = self.driver.find_element_by_id("playback-reporting-orbits")

        assert playback_reporting_orbits.text == "Mission S2A: 16066 - 16072 (7)"

        playback_used_orbits = self.driver.find_element_by_id("playback-used-orbits")

        assert playback_used_orbits.text == "Mission S2A: 16066 - 16071 (3)"

        ## Definite Mission

        ### Station Duration

        playback_S2A_station_duration = self.driver.find_element_by_id("playback-station-duration-S2A")

        SGS_total_average = playback_S2A_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'SGS_']]/td[2]")

        assert SGS_total_average.text == "3.335"

        SGS_net_average = playback_S2A_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'SGS_']]/td[3]")

        assert SGS_net_average.text == "11.671"

        SGS_minimum = playback_S2A_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'SGS_']]/td[4]")

        assert SGS_minimum.text == "11.645"

        SGS_maximum = playback_S2A_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'SGS_']]/td[5]")

        assert SGS_maximum.text == "11.697"

        EDRS_total_average = playback_S2A_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'EDRS']]/td[2]")

        assert EDRS_total_average.text == "2.232"

        EDRS_net_average = playback_S2A_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'EDRS']]/td[3]")

        assert EDRS_net_average.text == "15.625"

        EDRS_minimum = playback_S2A_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'EDRS']]/td[4]")

        assert EDRS_minimum.text == "15.625"

        EDRS_maximum = playback_S2A_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'EDRS']]/td[5]")

        assert EDRS_maximum.text == "15.625"

        ### Total duration

        playback_S2A_total_duration = self.driver.find_element_by_id("playback-total-duration-S2A")

        total_duration = playback_S2A_total_duration.find_element_by_xpath("tbody/tr[th[text() = 'Total(m):']]/td[1]")

        assert total_duration.text == "38.968"

        total_average = playback_S2A_total_duration.find_element_by_xpath("tbody/tr[th[text() = 'Total average(m):']]/td[1]")

        assert total_average.text == "5.567"

        net_average = playback_S2A_total_duration.find_element_by_xpath("tbody/tr[th[text() = 'Net average(m):']]/td[1]")

        assert net_average.text == "12.989"

        minimum = playback_S2A_total_duration.find_element_by_xpath("tbody/tr[th[text() = 'Minimum(m):']]/td[1]")

        assert minimum.text == "11.645"

        maximum = playback_S2A_total_duration.find_element_by_xpath("tbody/tr[th[text() = 'Maximum(m):']]/td[1]")

        assert maximum.text == "15.625"

        ## All Missions

        ### Station duration

        playback_all_station_duration = self.driver.find_element_by_id("playback-station-duration-S2")

        SGS_total_average = playback_all_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'SGS_']]/td[2]")

        assert SGS_total_average.text == "3.335"

        SGS_net_average = playback_all_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'SGS_']]/td[3]")

        assert SGS_net_average.text == "11.671"

        SGS_minimum = playback_all_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'SGS_']]/td[4]")

        assert SGS_minimum.text == "11.645"

        SGS_maximum = playback_all_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'SGS_']]/td[5]")

        assert SGS_maximum.text == "11.697"

        EDRS_total_average = playback_all_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'EDRS']]/td[2]")

        assert EDRS_total_average.text == "2.232"

        EDRS_net_average = playback_all_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'EDRS']]/td[3]")

        assert EDRS_net_average.text == "15.625"

        EDRS_minimum = playback_all_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'EDRS']]/td[4]")

        assert EDRS_minimum.text == "15.625"

        EDRS_maximum = playback_all_station_duration.find_element_by_xpath("tbody/tr[td[text() = 'EDRS']]/td[5]")

        assert EDRS_maximum.text == "15.625"

        ### Total duration

        playback_all_total_duration = self.driver.find_element_by_id("playback-total-duration-S2")

        total_duration = playback_all_total_duration.find_element_by_xpath("tbody/tr[th[text() = 'Total(m):']]/td[1]")

        assert total_duration.text == "38.968"

        total_average = playback_all_total_duration.find_element_by_xpath("tbody/tr[th[text() = 'Total average(m):']]/td[1]")

        assert total_average.text == "5.567"

        net_average = playback_all_total_duration.find_element_by_xpath("tbody/tr[th[text() = 'Net average(m):']]/td[1]")

        assert net_average.text == "12.989"

        minimum = playback_all_total_duration.find_element_by_xpath("tbody/tr[th[text() = 'Minimum(m):']]/td[1]")

        assert minimum.text == "11.645"

        maximum = playback_all_total_duration.find_element_by_xpath("tbody/tr[th[text() = 'Maximum(m):']]/td[1]")

        assert maximum.text == "15.625"

        # Graph duration playbacks

        playback_events = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_PLAYBACK", "op": "=="},
                                                        value_filters = [{"name": {"filter": "playback_type", "op": "=="},
                                                                        "type": "text",
                                                                        "value": {"op": "in", "filter": ["NOMINAL", "REGULAR", "RT", "NRT"]}}])

        playback_events.sort(key=lambda x:x.start, reverse=True)

        playback_xy_events = [
        {
            "id": str(playback_events[0].event_uuid),
            "group": "S2A",
            "x": "2018-07-20 23:30:09.608524",
            "y": "15.625495066666668",
            "tooltip": "<table border='1'>" +
                "<tr><td>UUID</td><td>" + str(playback_events[0].event_uuid) + "</td></tr>" +
                "<tr><td>Satellite</td><td>S2A</td></tr>" +
                "<tr><td>Orbit</td><td>16071</td></tr>" +
                "<tr><td>Station</td><td>EDRS</td></tr>" +
                "<tr><td>Start</td><td>2018-07-20T23:30:09.608524</td></tr>" +
                "<tr><td>Stop</td><td>2018-07-20T23:45:47.138228</td></tr>" +
                "<tr><td>Duration(m)</td><td>15.626</td></tr>" +
                "<tr><td>Playback type</td><td>NRT</td></tr>" +
                "<tr><td>Playback mean</td><td>OCP</td></tr>" +
                "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(playback_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                "</table>"
        },
        {
            "id": str(playback_events[1].event_uuid),
            "group": "S2A",
            "x": "2018-07-20 15:41:58.393742",
            "y": "11.644958966666668",
            "tooltip": "<table border='1'>" +
                "<tr><td>UUID</td><td>" + str(playback_events[1].event_uuid) + "</td></tr>" +
                "<tr><td>Satellite</td><td>S2A</td></tr>" +
                "<tr><td>Orbit</td><td>16067</td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Start</td><td>2018-07-20T15:41:58.393742</td></tr>" +
                "<tr><td>Stop</td><td>2018-07-20T15:53:37.091280</td></tr>" +
                "<tr><td>Duration(m)</td><td>11.645</td></tr>" +
                "<tr><td>Playback type</td><td>RT</td></tr>" +
                "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(playback_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                "</table>"
        },
        {
            "id": str(playback_events[2].event_uuid),
            "group": "S2A",
            "x": "2018-07-20 14:02:38.392053",
            "y": "11.697489133333333",
            "tooltip": "<table border='1'>" +
                "<tr><td>UUID</td><td>" + str(playback_events[2].event_uuid) + "</td></tr>" +
                "<tr><td>Satellite</td><td>S2A</td></tr>" +
                "<tr><td>Orbit</td><td>16066</td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Start</td><td>2018-07-20T14:02:38.392053</td></tr>" +
                "<tr><td>Stop</td><td>2018-07-20T14:14:20.241401</td></tr>" +
                "<tr><td>Duration(m)</td><td>11.697</td></tr>" +
                "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(playback_events[2].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                "</table>"
        }
        ]

        assert self.driver.execute_script('return playback_xy_events;') == playback_xy_events

        ## Playback details

        playback_details_table = self.driver.find_element_by_id("playback-details-table")

        playback_details_satellite = playback_details_table.find_element_by_xpath("tbody/tr[last()]/td[1]").text

        assert playback_details_satellite == "S2A"

        playback_details_orbit = playback_details_table.find_element_by_xpath("tbody/tr[last()]/td[2]").text

        assert playback_details_orbit == "16066"

        playback_details_station = playback_details_table.find_element_by_xpath("tbody/tr[last()]/td[3]").text

        assert playback_details_station == "SGS_"

        playback_details_start = playback_details_table.find_element_by_xpath("tbody/tr[last()]/td[4]").text

        assert playback_details_start == "2018-07-20T14:02:38.392053"

        playback_details_stop = playback_details_table.find_element_by_xpath("tbody/tr[last()]/td[5]").text

        assert playback_details_stop == "2018-07-20T14:14:20.241401"

        playback_details_duration_s = playback_details_table.find_element_by_xpath("tbody/tr[last()]/td[6]").text

        assert playback_details_duration_s == "701.849"

        playback_details_duration_m = playback_details_table.find_element_by_xpath("tbody/tr[last()]/td[7]").text

        assert playback_details_duration_m == "11.697"

        playback_details_playback_mode = playback_details_table.find_element_by_xpath("tbody/tr[last()]/td[8]").text

        assert playback_details_playback_mode == "NOMINAL"

        playback_details_parameters = playback_details_table.find_element_by_xpath("tbody/tr[last()]/td[9]").text

        assert playback_details_parameters == "MEM_FREE=1\nSCN_DUP=0\nSCN_RWD=1"

        playback_details_plan_file = playback_details_table.find_element_by_xpath("tbody/tr[last()]/td[10]").text

        assert playback_details_plan_file == "S2A_NPPF.EOF"

        playback_details_uuid = playback_details_table.find_element_by_xpath("tbody/tr[last()]/td[12]").text

        assert re.match("........-....-....-....-............", playback_details_uuid)

        # Timeline

        imaging_events = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="})

        imaging_events.sort(key=lambda x:x.start, reverse=True)

        imaging_timeline_events = [
        {
            "id": str(imaging_events[0].event_uuid),
            "group": "S2A",
            "timeline": "PLANNED_CUT_IMAGING",
            "start": "2018-07-20 17:28:56.736288",
            "stop": "2018-07-20 17:48:46.333653",
            "tooltip":"<table border='1'>" +
                        "<tr><td>UUID</td><td>" + str(imaging_events[0].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16068</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T17:28:56.736288</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T17:48:46.333653</td></tr>" +
                        "<tr><td>Duration(m)</td><td>19.827</td></tr>" +
                        "<tr><td>Imaging mode</td><td>TEST</td></tr>" +
                        "<tr><td>Record type</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(imaging_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        },
        {
            "id": str(imaging_events[1].event_uuid),
            "group": "S2A",
            "timeline": "PLANNED_CUT_IMAGING",
            "start": "2018-07-20 16:05:09.432097",
            "stop": "2018-07-20 16:11:19.936109",
            "tooltip": "<table border='1'>" +
                        "<tr><td>UUID</td><td>"+ str(imaging_events[1].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16067</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T16:05:09.432097</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T16:11:19.936109</td></tr>" +
                        "<tr><td>Duration(m)</td><td>6.175</td></tr>" +
                        "<tr><td>Imaging mode</td><td>RAW</td></tr>" +
                        "<tr><td>Record type</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(imaging_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        },
        {
            "id": str(imaging_events[2].event_uuid),
            "group": "S2A",
            "timeline": "PLANNED_CUT_IMAGING",
            "start": "2018-07-20 15:49:02.890406",
            "stop": "2018-07-20 16:04:25.078599",
            "tooltip": "<table border='1'>" +
                        "<tr><td>UUID</td><td>" + str(imaging_events[2].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16067</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T15:49:02.890406</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T16:04:25.078599</td></tr>" +
                        "<tr><td>Duration(m)</td><td>15.370</td></tr>" +
                        "<tr><td>Imaging mode</td><td>VICARIOUS_CAL</td></tr>" +
                        "<tr><td>Record type</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(imaging_events[2].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        },
        {
            "id": str(imaging_events[3].event_uuid),
            "group": "S2A",
            "timeline": "PLANNED_CUT_IMAGING",
            "start": "2018-07-20 15:48:09.150610",
            "stop": "2018-07-20 15:48:29.722723",
            "tooltip":  "<table border='1'>" +
                        "<tr><td>UUID</td><td>" + str(imaging_events[3].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16067</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T15:48:09.150610</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T15:48:29.722723</td></tr>" +
                        "<tr><td>Duration(m)</td><td>0.343</td></tr>" +
                        "<tr><td>Imaging mode</td><td>DARK_CAL_CSM_CLOSE</td></tr>" +
                        "<tr><td>Record type</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(imaging_events[3].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        },
        {
            "id": str(imaging_events[4].event_uuid),
            "group": "S2A",
            "timeline": "PLANNED_CUT_IMAGING",
            "start": "2018-07-20 14:27:50.784884",
            "stop": "2018-07-20 14:47:59.855425",
            "tooltip": "<table border='1'>" +
                        "<tr><td>UUID</td><td>" + str(imaging_events[4].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16066</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T14:27:50.784884</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T14:47:59.855425</td></tr>" +
                        "<tr><td>Duration(m)</td><td>20.151</td></tr>" +
                        "<tr><td>Imaging mode</td><td>DARK_CAL_CSM_OPEN</td></tr>" +
                        "<tr><td>Record type</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(imaging_events[4].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        },
        {
            "id": str(imaging_events[5].event_uuid),
            "group": "S2A",
            "timeline": "PLANNED_CUT_IMAGING",
            "start": "2018-07-20 14:10:02.951732",
            "stop": "2018-07-20 14:16:10.071190",
            "tooltip": "<table border='1'>" +
                        "<tr><td>UUID</td><td>" + str(imaging_events[5].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16066</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T14:10:02.951732</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T14:16:10.071190</td></tr>" +
                        "<tr><td>Duration(m)</td><td>6.119</td></tr>" +
                        "<tr><td>Imaging mode</td><td>SUN_CAL</td></tr>" +
                        "<tr><td>Record type</td><td>NRT</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(imaging_events[5].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        },
        {
            "id": str(imaging_events[6].event_uuid),
            "group": "S2A",
            "timeline": "PLANNED_CUT_IMAGING",
            "start": "2018-07-20 14:07:32.793311",
            "stop": "2018-07-20 14:08:58.407047",
            "tooltip": "<table border='1'>" +
                        "<tr><td>UUID</td><td>" + str(imaging_events[6].event_uuid) + "</td></tr>" +
                        "<tr><td>Satellite</td><td>S2A</td></tr>" +
                        "<tr><td>Orbit</td><td>16066</td></tr>" +
                        "<tr><td>Start</td><td>2018-07-20T14:07:32.793311</td></tr>" +
                        "<tr><td>Stop</td><td>2018-07-20T14:08:58.407047</td></tr>" +
                        "<tr><td>Duration(m)</td><td>1.427</td></tr>" +
                        "<tr><td>Imaging mode</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Record type</td><td>NOMINAL</td></tr>" +
                        "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                        '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(imaging_events[6].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                        "</table>"

        }
        ]

        assert self.driver.execute_script('return imaging_timeline_events;') == imaging_timeline_events

        playback_events = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_PLAYBACK", "op": "=="})

        playback_events.sort(key=lambda x:x.start, reverse=True)

        playback_timeline_events = [
        {
            "id": str(playback_events[0].event_uuid),
            "group": "S2A",
            "timeline": "PLANNED_PLAYBACK",
            "start": "2018-07-20 23:45:58.144267",
            "stop": "2018-07-20 23:45:58.144267",
            "tooltip": "<table border='1'>" +
                "<tr><td>UUID</td><td>" + str(playback_events[0].event_uuid) + "</td></tr>" +
                "<tr><td>Satellite</td><td>S2A</td></tr>" +
                "<tr><td>Orbit</td><td>16071</td></tr>" +
                "<tr><td>Station</td><td>EDRS</td></tr>" +
                "<tr><td>Start</td><td>2018-07-20T23:45:58.144267</td></tr>" +
                "<tr><td>Stop</td><td>2018-07-20T23:45:58.144267</td></tr>" +
                "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                "<tr><td>Playback type</td><td>SAD</td></tr>" +
                "<tr><td>Playback mean</td><td>OCP</td></tr>" +
                "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(playback_events[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                "</table>"
        },
        {
            "id": str(playback_events[1].event_uuid),
            "group": "S2A",
            "timeline": "PLANNED_PLAYBACK",
            "start": "2018-07-20 23:30:09.608524",
            "stop": "2018-07-20 23:45:47.138228",
            "tooltip": "<table border='1'>" +
                "<tr><td>UUID</td><td>" + str(playback_events[1].event_uuid) + "</td></tr>" +
                "<tr><td>Satellite</td><td>S2A</td></tr>" +
                "<tr><td>Orbit</td><td>16071</td></tr>" +
                "<tr><td>Station</td><td>EDRS</td></tr>" +
                "<tr><td>Start</td><td>2018-07-20T23:30:09.608524</td></tr>" +
                "<tr><td>Stop</td><td>2018-07-20T23:45:47.138228</td></tr>" +
                "<tr><td>Duration(m)</td><td>15.626</td></tr>" +
                "<tr><td>Playback type</td><td>NRT</td></tr>" +
                "<tr><td>Playback mean</td><td>OCP</td></tr>" +
                "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(playback_events[1].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                "</table>"
        },
        {
            "id": str(playback_events[2].event_uuid),
            "group": "S2A",
            "timeline": "PLANNED_PLAYBACK",
            "start": "2018-07-20 15:53:48.098255",
            "stop": "2018-07-20 15:53:48.098255",
            "tooltip": "<table border='1'>" +
                "<tr><td>UUID</td><td>" + str(playback_events[2].event_uuid) + "</td></tr>" +
                "<tr><td>Satellite</td><td>S2A</td></tr>" +
                "<tr><td>Orbit</td><td>16067</td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Start</td><td>2018-07-20T15:53:48.098255</td></tr>" +
                "<tr><td>Stop</td><td>2018-07-20T15:53:48.098255</td></tr>" +
                "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                "<tr><td>Playback type</td><td>HKTM_SAD</td></tr>" +
                "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(playback_events[2].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                "</table>"
        },
        {
            "id": str(playback_events[3].event_uuid),
            "group": "S2A",
            "timeline": "PLANNED_PLAYBACK",
            "start": "2018-07-20 15:41:58.393742",
            "stop": "2018-07-20 15:53:37.091280",
            "tooltip": "<table border='1'>" +
                "<tr><td>UUID</td><td>" + str(playback_events[3].event_uuid) + "</td></tr>" +
                "<tr><td>Satellite</td><td>S2A</td></tr>" +
                "<tr><td>Orbit</td><td>16067</td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Start</td><td>2018-07-20T15:41:58.393742</td></tr>" +
                "<tr><td>Stop</td><td>2018-07-20T15:53:37.091280</td></tr>" +
                "<tr><td>Duration(m)</td><td>11.645</td></tr>" +
                "<tr><td>Playback type</td><td>RT</td></tr>" +
                "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(playback_events[3].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                "</table>"
        },
        {
            "id": str(playback_events[4].event_uuid),
            "group": "S2A",
            "timeline": "PLANNED_PLAYBACK",
            "start": "2018-07-20 14:14:31.243397",
            "stop": "2018-07-20 14:14:31.243397",
            "tooltip": "<table border='1'>" +
                "<tr><td>UUID</td><td>" + str(playback_events[4].event_uuid) + "</td></tr>" +
                "<tr><td>Satellite</td><td>S2A</td></tr>" +
                "<tr><td>Orbit</td><td>16066</td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Start</td><td>2018-07-20T14:14:31.243397</td></tr>" +
                "<tr><td>Stop</td><td>2018-07-20T14:14:31.243397</td></tr>" +
                "<tr><td>Duration(m)</td><td>0.000</td></tr>" +
                "<tr><td>Playback type</td><td>HKTM_SAD</td></tr>" +
                "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(playback_events[4].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                "</table>"
        },
        {
            "id": str(playback_events[5].event_uuid),
            "group": "S2A",
            "timeline": "PLANNED_PLAYBACK",
            "start": "2018-07-20 14:02:38.392053",
            "stop": "2018-07-20 14:14:20.241401",
            "tooltip": "<table border='1'>" +
                "<tr><td>UUID</td><td>" + str(playback_events[5].event_uuid) + "</td></tr>" +
                "<tr><td>Satellite</td><td>S2A</td></tr>" +
                "<tr><td>Orbit</td><td>16066</td></tr>" +
                "<tr><td>Station</td><td>SGS_</td></tr>" +
                "<tr><td>Start</td><td>2018-07-20T14:02:38.392053</td></tr>" +
                "<tr><td>Stop</td><td>2018-07-20T14:14:20.241401</td></tr>" +
                "<tr><td>Duration(m)</td><td>11.697</td></tr>" +
                "<tr><td>Playback type</td><td>NOMINAL</td></tr>" +
                "<tr><td>Playback mean</td><td>XBAND</td></tr>" +
                "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" +
                '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/' + str(playback_events[5].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' +
                "</table>"
        }]

        assert self.driver.execute_script('return playback_timeline_events;') == playback_timeline_events

    def test_planning_query(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_MPL_SPSGS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2_SRA_EDRS_A.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_slot_request_edrs.ingestion_slot_request_edrs", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        wait = WebDriverWait(self.driver,5);

        # Only start

        self.driver.get("http://localhost:5000/views/planning")

        functions.query(self.driver, wait, "S2A", start = "2030-07-01T00:00:00")

        assert functions.page_loaded(self.driver, wait, "header-no-data")

        # Only stop

        self.driver.get("http://localhost:5000/views/planning")

        functions.query(self.driver, wait, "S2A", stop = "2008-07-31T23:59:59")

        assert functions.page_loaded(self.driver, wait, "header-no-data")

        #Only period

        self.driver.get("http://localhost:5000/views/planning")

        functions.query(self.driver, wait, "S2A", start = "2008-07-31T23:59:59", stop = "2008-07-31T23:59:59")

        assert functions.page_loaded(self.driver, wait, "header-no-data")

        # Only start_orbit

        self.driver.get("http://localhost:5000/views/planning")

        functions.query(self.driver, wait, "S2A", start_orbit = "16600")

        assert functions.page_loaded(self.driver, wait, "header-no-data")

        # Only stop_orbit

        self.driver.get("http://localhost:5000/views/planning")

        functions.query(self.driver, wait, "S2A", stop_orbit = "17800")

        functions.page_loaded(self.driver, wait, "header-no-data")

        #Only orbits

        self.driver.get("http://localhost:5000/views/planning")

        functions.query(self.driver, wait, "S2A", start_orbit = "17800", stop_orbit = "17800")

        functions.page_loaded(self.driver, wait, "header-no-data")

        # No filter

        self.driver.get("http://localhost:5000/views/planning")

        functions.query(self.driver,wait)

        assert functions.page_loaded(self.driver, wait, "header-no-data")

        # Different mission

        self.driver.get("http://localhost:5000/views/planning")

        functions.query(self.driver,wait, mission = "S2B")

        assert functions.page_loaded(self.driver, wait, "header-no-data")

        # No graphs

        self.driver.get("http://localhost:5000/views/planning")

        functions.query(self.driver,wait, timeline = False, table_details = False, evolution = False, map = False)

        assert functions.page_loaded(self.driver, wait, "header-no-data")


    def test_planning_only_nppf_and_orbpre_removed_nppf(self):
        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        self.query_eboa.get_sources(names = {"filter": filename, "op": "=="}, delete=True)

        wait = WebDriverWait(self.driver,5);

        self.driver.get("http://localhost:5000/views/planning")

        functions.query(self.driver, wait, "S2A", start = "2018-07-20T00:00:14", stop = "2018-07-21T23:55:14", start_orbit = "16066", stop_orbit = "16072", timeline = True, table_details = True, evolution = True, map = True)

        # Check that sections are empty

        summary_no_data = wait.until(EC.visibility_of_element_located((By.ID,"summary-no-imaging")))

        assert summary_no_data

        imaging_no_data = wait.until(EC.visibility_of_element_located((By.ID,"imaging-no-imaging")))

        assert imaging_no_data

        playback_no_data = wait.until(EC.visibility_of_element_located((By.ID,"playback-no-playback")))

        assert playback_no_data

        timeline_no_data = wait.until(EC.visibility_of_element_located((By.ID,"timeline-no-planning")))

        assert timeline_no_data
