"""
Automated tests for the DHUS completeness view

Written by DEIMOS Space S.L. (femd)

module vboa
"""
import os
import sys
import unittest
import time
import subprocess
import datetime
import s2vboa.tests.dhus_completeness.aux_functions as functions
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


class TestDhusCompletenessView(unittest.TestCase):
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

    def test_dhus_completeness_no_data(self):

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/dhus-completeness")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "17600", stop_orbit = "17800", table_details = True, map = True, station_reports = True)

        # Check header generated
        header_no_data = wait.until(EC.visibility_of_element_located((By.ID,"header-no-data")))

        assert header_no_data

        table_details_no_data = wait.until(EC.visibility_of_element_located((By.ID,"dhus-completeness-no-expected-dissemination")))

        assert table_details_no_data

    def test_dhus_completeness(self):

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

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L1B_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPDAM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dam.ingestion_dam", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____MPS__20180721T110232_V20180721T085229_20180721T085414.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]
        
        filename = "S2__OPDHUS.xml"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dhus.ingestion_dhus", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "test_input_file_containing_dhus_publication_timings.xml"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_publication_dhus.ingestion_publication_dhus", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/dhus-completeness")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "17600", stop_orbit = "17800", table_details = True, map = True, station_reports = True)

        # Check summary expected msi
        summary_expected_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-expected-msi")))

        assert summary_expected_msi

        assert summary_expected_msi.text == "33.033"

        # Check summary acquired msi
        summary_acquired_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-acquired-msi")))

        assert summary_acquired_msi

        assert summary_acquired_msi.text == "1.804"

        # Check summary processed to l1c msi
        summary_processed_l1c_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-processed-to-l1c-msi")))

        assert summary_processed_l1c_msi

        assert summary_processed_l1c_msi.text == "1.833"

        # Check summary processed to l2a msi
        summary_processed_l2a_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-processed-to-l2a-msi")))

        assert summary_processed_l2a_msi

        assert summary_processed_l2a_msi.text == "0.0"

        # Check summary generated to l1c tiles
        summary_generated_l1c_tiles = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-generated-l1c-tiles")))

        assert summary_generated_l1c_tiles

        assert summary_generated_l1c_tiles.text == "4"

        # Check summary generated to l2a tiles
        summary_generated_l2a_tiles = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-generated-l2a-tiles")))

        assert summary_generated_l2a_tiles

        assert summary_generated_l2a_tiles.text == "0"

        # Check summary missing acquistion
        summary_missing_acquistion = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-acquistion")))

        assert summary_missing_acquistion

        assert summary_missing_acquistion.text == "30.895"

        # Check summary missing processing l1c
        summary_missing_processing_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-processing-l1c")))

        assert summary_missing_processing_l1c

        assert summary_missing_processing_l1c.text == "30.866"

        # Check summary missing processing l2a
        summary_missing_processing_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-processing-l2a")))

        assert summary_missing_processing_l2a

        assert summary_missing_processing_l2a.text == "32.699"

        # Check summary missing l1c tiles in DAM
        summary_missing_l1c_tiles_dam = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-l1c-tiles-in-dam")))

        assert summary_missing_l1c_tiles_dam

        assert summary_missing_l1c_tiles_dam.text == "1"

        # Check summary missing l1c tiles in DHUS
        summary_missing_l1c_tiles_dhus = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-l1c-tiles-in-dhus")))

        assert summary_missing_l1c_tiles_dhus

        assert summary_missing_l1c_tiles_dhus.text == "2"

        # Check summary missing l1c tiles published in DHUS
        summary_missing_l1c_tiles_published_dhus = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-l1c-tiles-published-in-dhus")))

        assert summary_missing_l1c_tiles_published_dhus

        assert summary_missing_l1c_tiles_published_dhus.text == "3"

        # Check number of elements in summary
        assert len(summary_expected_msi.find_elements_by_xpath("../../../div")) == 12

        # Check whether the map is displayed
        map_section = self.driver.find_element_by_id("dhus-completeness-on-map-section")

        condition = map_section.is_displayed()

        assert condition is True

        l1c_map_section = self.driver.find_element_by_id("dhus-completeness-l1c-on-map-section")

        condition = l1c_map_section.is_displayed()

        assert condition is True

        l2a_map_section = self.driver.find_element_by_id("dhus-completeness-l2a-on-map-section")

        condition = l2a_map_section.is_displayed()

        assert condition is True

        # Check map missing segments tooltip
        planned_imaging_processing_completeness_l2a = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L2A", "op":"=="})
        planned_imaging_correction = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_CUT_IMAGING_CORRECTION", "op":"=="})
        planned_cut_imaging = self.query_eboa.get_events(gauge_names ={"filter": "PLANNED_CUT_IMAGING", "op":"=="})

        map_l2a_tooltip_info = [
            {
                "id": str(planned_imaging_processing_completeness_l2a[0].event_uuid),
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(planned_imaging_processing_completeness_l2a[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr><tr>" + 
                "<td>Orbit</td><td>16077</td></tr>" + 
                "<tr><td>Datastrip</td><td>N/A</td></tr>" + 
                "<tr><td>Status</td><td><a class='bold-red' href='/views/dhus-completeness-by-datatake/" + str(planned_imaging_correction[0].event_uuid) + "'>MISSING ACQUISITION</a></td></tr>" + 
                "<tr><td>Start</td><td>2018-07-21T08:36:08.255634</td></tr>" + 
                "<tr><td>Stop</td><td>2018-07-21T09:08:50.195941</td></tr>" + 
                "<tr><td>Duration(m)</td><td>32.699</td></tr>" + 
                "<tr><td>Plan file</td><td>S2A_NPPF.EOF</td></tr>" + 
                '<tr><td>Planned imaging</td><td><a href="/eboa_nav/query-event-links/' + str(planned_cut_imaging[0].event_uuid) + '"><i class="fa fa-link"></i></a></td></tr>' + 
                "</table>",
                "geometries": [
                        {'value': 'POLYGON ((101.528355 79.738353, 98.393294 79.554394, 95.372456 79.34158499999999, 92.47433599999999 79.101615, 89.704358 78.83623299999999, 87.065195 78.547203, 84.557168 78.236266, 82.178646 77.905114, 79.92652200000001 77.555353, 77.796533 77.188502, 75.78361 76.80598500000001, 73.882164 76.409121, 72.086314 75.999127, 70.390066 75.577118, 68.787451 75.144115, 67.27263000000001 74.701048, 65.839963 74.248763, 64.484058 73.788026, 63.199803 73.319535, 61.98238 72.84392099999999, 60.82727 72.361756, 59.730252 71.87356, 58.687393 71.379802, 57.69504 70.880909, 56.749802 70.377269, 55.848538 69.86923400000001, 54.988339 69.357125, 54.166514 68.841234, 53.380572 68.321826, 52.628211 67.799145, 51.907284 67.273414, 51.215837 66.74483499999999, 50.552046 66.21359200000001, 49.914221 65.679856, 49.300795 65.14378499999999, 48.710317 64.605521, 48.141439 64.06519900000001, 47.592911 63.522938, 47.063571 62.978854, 46.552336 62.433049, 46.058203 61.88562, 45.580233 61.336656, 45.117553 60.786241, 44.669348 60.23445, 44.234857 59.681356, 43.813369 59.127025, 43.404219 58.571519, 43.006785 58.014895, 42.620482 57.457208, 42.244763 56.898507, 41.879116 56.33884, 41.523059 55.778251, 41.176136 55.216781, 40.837913 54.65447, 40.507999 54.091353, 40.186016 53.527465, 39.871607 52.962837, 39.564437 52.3975, 39.264186 51.831483, 38.970556 51.264812, 38.683263 50.697513, 38.402038 50.12961, 38.126626 49.561125, 37.856788 48.992081, 37.592294 48.422497, 37.332928 47.852393, 37.078485 47.281788, 36.828768 46.710698, 36.583593 46.139141, 36.342781 45.567132, 36.106166 44.994686, 35.873587 44.421818, 35.644892 43.848541, 35.419934 43.274869, 35.198576 42.700813, 34.980684 42.126386, 34.766127 41.5516, 34.554789 40.976465, 34.346555 40.400992, 34.141315 39.825191, 33.938963 39.249071, 33.739397 38.672642, 33.542521 38.095913, 33.348241 37.518892, 33.156469 36.941588, 32.967118 36.364009, 32.780106 35.786163, 32.595355 35.208056, 32.412788 34.629697, 32.232333 34.051093, 32.053919 33.472249, 31.877479 32.893174, 31.702948 32.313873, 31.530263 31.734352, 31.359365 31.154617, 31.190194 30.574676, 31.022695 29.994532, 30.856813 29.414192, 30.692496 28.833661, 30.52969 28.252945, 30.368351 27.672049, 30.208431 27.090977, 30.049883 26.509735, 29.892665 25.928328, 29.736733 25.34676, 29.582046 24.765036, 29.428563 24.183161, 29.276246 23.601139, 29.125056 23.018975, 28.974958 22.436672, 28.825915 21.854236, 28.677892 21.27167, 28.530857 20.688979, 28.384776 20.106167, 28.239618 19.523237, 28.095351 18.940194, 27.951945 18.357042, 27.809371 17.773784, 27.667601 17.190425, 27.526605 16.606967, 27.386357 16.023415, 27.24683 15.439774, 27.107997 14.856045, 26.969834 14.272233, 26.832316 13.688341, 26.695417 13.104374, 26.559115 12.520334, 26.423385 11.936225, 26.288205 11.352051, 26.153552 10.767815, 26.019404 10.18352, 25.885738 9.599170000000001, 25.752535 9.014768, 25.619771 8.430318, 25.487428 7.845822, 25.355483 7.261285, 25.223917 6.676709, 25.092711 6.092098, 24.961844 5.507454, 24.831296 4.922782, 24.701049 4.338085, 24.571084 3.753365, 24.441382 3.168625, 24.311923 2.58387, 24.182691 1.999102, 24.053667 1.414324, 23.924832 0.8295400000000001, 23.796168 0.244752, 23.667656 -0.340037, 23.53928 -0.924823, 23.411021 -1.509603, 23.282861 -2.094374, 23.154782 -2.679134, 23.026766 -3.263878, 22.898797 -3.848605, 22.770855 -4.433311, 22.642923 -5.017993, 22.514983 -5.602648, 22.387017 -6.187273, 22.259008 -6.771866, 22.130936 -7.356423, 22.002785 -7.940941, 21.874535 -8.525416999999999, 21.746168 -9.109848, 21.617666 -9.694233000000001, 21.489009 -10.278566, 21.36018 -10.862846, 21.231159 -11.44707, 21.10193 -12.031235, 20.972471 -12.615337, 20.84276 -13.199375, 20.712779 -13.783345, 20.582507 -14.367243, 20.451923 -14.951069, 20.321007 -15.534817, 20.189737 -16.118486, 20.058092 -16.702073, 19.926048 -17.285575, 19.793585 -17.868989, 19.660679 -18.452311, 19.527306 -19.03554, 19.393443 -19.618672, 19.259065 -20.201704, 19.124148 -20.784634, 18.988665 -21.367458, 18.852591 -21.950174, 18.7159 -22.532779, 18.578563 -23.115269, 18.440552 -23.697642, 18.301839 -24.279894, 18.162396 -24.862023, 18.022195 -25.444026, 17.8812 -26.0259, 17.73938 -26.607641, 17.596701 -27.189247, 17.453128 -27.770714, 17.308628 -28.352039, 17.163163 -28.933219, 17.016695 -29.514251, 16.869187 -30.095131, 13.933539 -29.491417, 14.098138 -28.912293, 14.261223 -28.33296, 14.422844 -27.753423, 14.583047 -27.173686, 14.741878 -26.593755, 14.89938 -26.013634, 15.055598 -25.433327, 15.210571 -24.852841, 15.36434 -24.272178, 15.516947 -23.691343, 15.668426 -23.11034, 15.818815 -22.529175, 15.968148 -21.94785, 16.116461 -21.36637, 16.263787 -20.784739, 16.410159 -20.202961, 16.555607 -19.62104, 16.700165 -19.038979, 16.843861 -18.456783, 16.986725 -17.874455, 17.128786 -17.292, 17.270072 -16.70942, 17.41061 -16.126719, 17.550427 -15.543901, 17.689548 -14.96097, 17.828001 -14.377929, 17.965808 -13.794781, 18.102996 -13.211531, 18.239588 -12.628181, 18.375607 -12.044735, 18.511076 -11.461196, 18.646018 -10.877568, 18.780456 -10.293853, 18.914411 -9.710056, 19.047904 -9.12618, 19.180957 -8.542228, 19.31359 -7.958203, 19.445824 -7.374108, 19.577679 -6.789947, 19.709176 -6.205723, 19.840332 -5.62144, 19.971169 -5.037099, 20.101706 -4.452706, 20.231961 -3.868262, 20.361954 -3.28377, 20.491703 -2.699235, 20.621226 -2.114659, 20.750543 -1.530045, 20.879671 -0.945397, 21.008628 -0.360717, 21.137434 0.223991, 21.266105 0.808725, 21.39466 1.393481, 21.523116 1.978257, 21.651492 2.563048, 21.779804 3.147853, 21.908071 3.732668, 22.03631 4.31749, 22.164541 4.902317, 22.29278 5.487144, 22.421046 6.071969, 22.549357 6.656789, 22.677731 7.241602, 22.806186 7.826403, 22.934741 8.41119, 23.063414 8.995960999999999, 23.192224 9.580711000000001, 23.321189 10.165439, 23.45033 10.750141, 23.579663 11.334813, 23.70921 11.919454, 23.83899 12.504061, 23.969023 13.088629, 24.099328 13.673157, 24.229927 14.257641, 24.36084 14.842078, 24.492088 15.426466, 24.623693 16.010801, 24.755672 16.59508, 24.888051 17.179302, 25.020852 17.763461, 25.1541 18.347556, 25.287817 18.931583, 25.422028 19.51554, 25.556756 20.099424, 25.692028 20.68323, 25.827869 21.266957, 25.964305 21.850601, 26.101363 22.43416, 26.23907 23.017629, 26.377456 23.601007, 26.516548 24.184289, 26.656377 24.767473, 26.796974 25.350556, 26.93837 25.933533, 27.080597 26.516404, 27.223689 27.099162, 27.367681 27.681807, 27.512607 28.264333, 27.658505 28.846738, 27.805411 29.429019, 27.95336 30.011172, 28.102397 30.593193, 28.252563 31.175079, 28.403902 31.756827, 28.556459 32.338431, 28.71028 32.91989, 28.865413 33.501198, 29.021907 34.082352, 29.179815 34.663347, 29.339189 35.244181, 29.500086 35.824848, 29.662563 36.405344, 29.82668 36.985665, 29.9925 37.565806, 30.160087 38.145763, 30.32951 38.72553, 30.500839 39.305103, 30.674149 39.884477, 30.849515 40.463646, 31.027018 41.042604, 31.206743 41.621347, 31.388777 42.199868, 31.573211 42.77816, 31.760133 43.356219, 31.94965 43.934037, 32.14187 44.511607, 32.336903 45.088922, 32.534866 45.665975, 32.73588 46.242756, 32.940074 46.819259, 33.147583 47.395475, 33.358548 47.971394, 33.573118 48.547006, 33.791452 49.122303, 34.013715 49.697273, 34.240083 50.271906, 34.470741 50.846188, 34.705884 51.420109, 34.94572 51.993655, 35.190468 52.566812, 35.440361 53.139565, 35.695644 53.711899, 35.95658 54.283798, 36.223446 54.855243, 36.496539 55.426215, 36.776173 55.996696, 37.062667 56.566664, 37.356393 57.136096, 37.657733 57.704968, 37.967096 58.273253, 38.284919 58.840923, 38.611667 59.407948, 38.947843 59.974297, 39.293984 60.539933, 39.650668 61.10482, 40.018516 61.668918, 40.398198 62.232182, 40.790436 62.794566, 41.196009 63.356018, 41.61576 63.916483, 42.050602 64.47590099999999, 42.501524 65.034205, 42.969599 65.591324, 43.455996 66.14718000000001, 43.961985 66.701688, 44.488952 67.25475299999999, 45.03841 67.806273, 45.612014 68.35613499999999, 46.211575 68.904214, 46.839057 69.45037499999999, 47.496664 69.99446399999999, 48.186803 70.536312, 48.91212 71.075732, 49.675538 71.612514, 50.480285 72.14642600000001, 51.329936 72.677209, 52.228449 73.20457, 53.180217 73.728182, 54.190117 74.247676, 55.263568 74.762637, 56.406592 75.272594, 57.625885 75.77701399999999, 58.928884 76.27529199999999, 60.323843 76.766739, 61.819901 77.25057, 63.427147 77.725889, 65.15666299999999 78.19167400000001, 67.02054699999999 78.646756, 69.03187800000001 79.0898, 71.204616 79.519285, 73.553397 79.93347900000001, 76.093174 80.330421, 78.83862000000001 80.707914, 81.803448 81.06348699999999, 84.999177 81.394426, 88.433741 81.69779, 92.109756 81.970454, 96.02262 82.209198, 101.528355 79.738353))', 'name': 'footprint'},
                ],
                "style": {
                    "stroke_color": "red",
                    "fill_color": "rgba(255,0,0,0.3)",
                }
            },
        ]

        returned_map_l2a_tooltip_info = self.driver.execute_script('return missing_segments;')
        assert map_l2a_tooltip_info == returned_map_l2a_tooltip_info

        # Check whether the timeliness is displayed
        timeline_section = self.driver.find_element_by_id("dhus-completeness-e2e-timeline-section")

        condition = timeline_section.is_displayed()

        assert condition is True

        l1c_timeline_section = self.driver.find_element_by_id("dhus-completeness-l1c-e2e-timeline-section")

        condition = l1c_timeline_section.is_displayed()

        assert condition is True

        l2a_timeline_section = self.driver.find_element_by_id("dhus-completeness-l2a-e2e-timeline-section")

        condition = l2a_timeline_section.is_displayed()

        assert condition is True

        # Check timeliness tooltip
        timeliness_l2a_tooltip_info = []

        returned_timeliness_l2a_tooltip_info = self.driver.execute_script('return e2e_timeliness_tiles_published_in_dhus;')
        assert timeliness_l2a_tooltip_info == returned_timeliness_l2a_tooltip_info

        # Missing dissemination table
        missing_table = self.driver.find_element_by_id("dhus-completeness-list-table-MISSING")

        # Row 1
        level = missing_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert level.text == "L1C"

        satellite = missing_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert satellite.text == "S2A"

        orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:54:19"

        stop_datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip.text == "N/A"

        status = missing_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = missing_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = missing_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = missing_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = missing_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = missing_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = missing_table.find_element_by_xpath("tbody/tr[1]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = missing_table.find_element_by_xpath("tbody/tr[1]/td[14]")

        assert datatake.text == "N/A"

        start_msi = missing_table.find_element_by_xpath("tbody/tr[1]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = missing_table.find_element_by_xpath("tbody/tr[1]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 2
        level = missing_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L1C"

        satellite = missing_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert satellite.text == "S2A"

        orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:52:29"

        stop_datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert stop_datastrip.text == "2018-07-21T08:54:19"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip.text == "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        status = missing_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert status.text == "MISSING DAM PUBLICATION"

        tiles = missing_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert tiles.text == "4"

        tiles_dam = missing_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert tiles_dam.text == "3"

        tiles_dhus = missing_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert tiles_dhus.text == "2"

        tiles_published_dhus = missing_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert tiles_published_dhus.text == "1"

        mean_time_dhus = missing_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert mean_time_dhus.text == "225.797"

        mean_time_dhus_publication = missing_table.find_element_by_xpath("tbody/tr[2]/td[13]")

        assert mean_time_dhus_publication.text == "1206891.184"

        datatake = missing_table.find_element_by_xpath("tbody/tr[2]/td[14]")

        assert datatake.text == "GS2A_20180721T083601_016077_N02.06"

        start_msi = missing_table.find_element_by_xpath("tbody/tr[2]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = missing_table.find_element_by_xpath("tbody/tr[2]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 3
        level = missing_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1C"

        satellite = missing_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert satellite.text == "S2A"

        orbit = missing_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = missing_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = missing_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert stop_datastrip.text == "2018-07-21T08:52:29"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip.text == "N/A"

        status = missing_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = missing_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = missing_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = missing_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = missing_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = missing_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = missing_table.find_element_by_xpath("tbody/tr[3]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = missing_table.find_element_by_xpath("tbody/tr[3]/td[14]")

        assert datatake.text == "N/A"

        start_msi = missing_table.find_element_by_xpath("tbody/tr[3]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = missing_table.find_element_by_xpath("tbody/tr[3]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 4
        level = missing_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L2A"

        satellite = missing_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert satellite.text == "S2A"

        orbit = missing_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = missing_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = missing_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip.text == "N/A"

        status = missing_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = missing_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = missing_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = missing_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = missing_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = missing_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = missing_table.find_element_by_xpath("tbody/tr[4]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = missing_table.find_element_by_xpath("tbody/tr[4]/td[14]")

        assert datatake.text == "N/A"

        start_msi = missing_table.find_element_by_xpath("tbody/tr[4]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = missing_table.find_element_by_xpath("tbody/tr[4]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Data availability table
        complete_table = self.driver.find_element_by_id("dhus-completeness-list-table-COMPLETE")

        # Row 1
        level = complete_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert level.text == "L1C"

        satellite = complete_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert satellite.text == "S2A"

        orbit = complete_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = complete_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:54:19"

        stop_datastrip = complete_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = complete_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip.text == "N/A"

        status = complete_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = complete_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = complete_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = complete_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = complete_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = complete_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = complete_table.find_element_by_xpath("tbody/tr[1]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = complete_table.find_element_by_xpath("tbody/tr[1]/td[14]")

        assert datatake.text == "N/A"

        start_msi = complete_table.find_element_by_xpath("tbody/tr[1]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = complete_table.find_element_by_xpath("tbody/tr[1]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 2
        level = complete_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L1C"

        satellite = complete_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert satellite.text == "S2A"

        orbit = complete_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = complete_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:52:29"

        stop_datastrip = complete_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert stop_datastrip.text == "2018-07-21T08:54:19"

        datastrip = complete_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip.text == "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        status = complete_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert status.text == "MISSING DAM PUBLICATION"

        tiles = complete_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert tiles.text == "4"

        tiles_dam = complete_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert tiles_dam.text == "3"

        tiles_dhus = complete_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert tiles_dhus.text == "2"

        tiles_published_dhus = complete_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert tiles_published_dhus.text == "1"

        mean_time_dhus = complete_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert mean_time_dhus.text == "225.797"

        mean_time_dhus_publication = complete_table.find_element_by_xpath("tbody/tr[2]/td[13]")

        assert mean_time_dhus_publication.text == "1206891.184"

        datatake = complete_table.find_element_by_xpath("tbody/tr[2]/td[14]")

        assert datatake.text == "GS2A_20180721T083601_016077_N02.06"

        start_msi = complete_table.find_element_by_xpath("tbody/tr[2]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = complete_table.find_element_by_xpath("tbody/tr[2]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 3
        level = complete_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1C"

        satellite = complete_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert satellite.text == "S2A"

        orbit = complete_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = complete_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = complete_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert stop_datastrip.text == "2018-07-21T08:52:29"

        datastrip = complete_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip.text == "N/A"

        status = complete_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = complete_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = complete_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = complete_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = complete_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = complete_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = complete_table.find_element_by_xpath("tbody/tr[3]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = complete_table.find_element_by_xpath("tbody/tr[3]/td[14]")

        assert datatake.text == "N/A"

        start_msi = complete_table.find_element_by_xpath("tbody/tr[3]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = complete_table.find_element_by_xpath("tbody/tr[3]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 4
        level = complete_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L2A"

        satellite = complete_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert satellite.text == "S2A"

        orbit = complete_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = complete_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = complete_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = complete_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip.text == "N/A"

        status = complete_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = complete_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = complete_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = complete_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = complete_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = complete_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = complete_table.find_element_by_xpath("tbody/tr[4]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = complete_table.find_element_by_xpath("tbody/tr[4]/td[14]")

        assert datatake.text == "N/A"

        start_msi = complete_table.find_element_by_xpath("tbody/tr[4]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = complete_table.find_element_by_xpath("tbody/tr[4]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

    def test_dhus_completeness_only_nppf_and_orbpre(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/dhus-completeness")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "17600", stop_orbit = "17800", table_details = True, map = True, station_reports = True)

        # Check summary expected msi
        summary_expected_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-expected-msi")))

        assert summary_expected_msi

        assert summary_expected_msi.text == "33.033"

        # Check summary acquired msi
        summary_acquired_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-acquired-msi")))

        assert summary_acquired_msi

        assert summary_acquired_msi.text == "0.0"

        # Check summary processed to l1c msi
        summary_processed_l1c_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-processed-to-l1c-msi")))

        assert summary_processed_l1c_msi

        assert summary_processed_l1c_msi.text == "0.0"

        # Check summary processed to l2a msi
        summary_processed_l2a_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-processed-to-l2a-msi")))

        assert summary_processed_l2a_msi

        assert summary_processed_l2a_msi.text == "0.0"

        # Check summary generated to l1c tiles
        summary_generated_l1c_tiles = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-generated-l1c-tiles")))

        assert summary_generated_l1c_tiles

        assert summary_generated_l1c_tiles.text == "0"

        # Check summary generated to l2a tiles
        summary_generated_l2a_tiles = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-generated-l2a-tiles")))

        assert summary_generated_l2a_tiles

        assert summary_generated_l2a_tiles.text == "0"

        # Check summary missing acquistion
        summary_missing_acquistion = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-acquistion")))

        assert summary_missing_acquistion

        assert summary_missing_acquistion.text == "32.699"

        # Check summary missing processing l1c
        summary_missing_processing_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-processing-l1c")))

        assert summary_missing_processing_l1c

        assert summary_missing_processing_l1c.text == "32.699"

        # Check summary missing processing l2a
        summary_missing_processing_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-processing-l2a")))

        assert summary_missing_processing_l2a

        assert summary_missing_processing_l2a.text == "32.699"

        # Check number of elements in summary
        assert len(summary_expected_msi.find_elements_by_xpath("../../../div")) == 9

        # Check whether the map is displayed
        map_section = self.driver.find_element_by_id("dhus-completeness-on-map-section")

        condition = map_section.is_displayed()

        assert condition is True

        l1c_map_section = self.driver.find_element_by_id("dhus-completeness-l1c-on-map-section")

        condition = l1c_map_section.is_displayed()

        assert condition is True

        l2a_map_section = self.driver.find_element_by_id("dhus-completeness-l2a-on-map-section")

        condition = l2a_map_section.is_displayed()

        assert condition is True

        # Check whether the timeliness is displayed
        timeline_section = self.driver.find_element_by_id("dhus-completeness-e2e-timeline-section")

        condition = timeline_section.is_displayed()

        assert condition is True

        l1c_timeline_section = self.driver.find_element_by_id("dhus-completeness-l1c-e2e-timeline-section")

        condition = l1c_timeline_section.is_displayed()

        assert condition is True

        l2a_timeline_section = self.driver.find_element_by_id("dhus-completeness-l2a-e2e-timeline-section")

        condition = l2a_timeline_section.is_displayed()

        assert condition is True

        # Missing dissemination table
        missing_table = self.driver.find_element_by_id("dhus-completeness-list-table-MISSING")

        # Row 1
        level = missing_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert level.text == "L1C"

        satellite = missing_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert satellite.text == "S2A"

        orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip.text == "N/A"

        status = missing_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = missing_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = missing_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = missing_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = missing_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = missing_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = missing_table.find_element_by_xpath("tbody/tr[1]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = missing_table.find_element_by_xpath("tbody/tr[1]/td[14]")

        assert datatake.text == "N/A"

        start_msi = missing_table.find_element_by_xpath("tbody/tr[1]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = missing_table.find_element_by_xpath("tbody/tr[1]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 2
        level = missing_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L2A"

        satellite = missing_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert satellite.text == "S2A"

        orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip.text == "N/A"

        status = missing_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = missing_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = missing_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = missing_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = missing_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = missing_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = missing_table.find_element_by_xpath("tbody/tr[2]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = missing_table.find_element_by_xpath("tbody/tr[2]/td[14]")

        assert datatake.text == "N/A"

        start_msi = missing_table.find_element_by_xpath("tbody/tr[2]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = missing_table.find_element_by_xpath("tbody/tr[2]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Data availability table
        complete_table = self.driver.find_element_by_id("dhus-completeness-list-table-COMPLETE")

        # Row 1
        level = complete_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert level.text == "L1C"

        satellite = complete_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert satellite.text == "S2A"

        orbit = complete_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = complete_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = complete_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = complete_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip.text == "N/A"

        status = complete_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = complete_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = complete_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = complete_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = complete_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = complete_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = complete_table.find_element_by_xpath("tbody/tr[1]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = complete_table.find_element_by_xpath("tbody/tr[1]/td[14]")

        assert datatake.text == "N/A"

        start_msi = complete_table.find_element_by_xpath("tbody/tr[1]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = complete_table.find_element_by_xpath("tbody/tr[1]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 2
        level = complete_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L2A"

        satellite = complete_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert satellite.text == "S2A"

        orbit = complete_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = complete_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = complete_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = complete_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip.text == "N/A"

        status = complete_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = complete_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = complete_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = complete_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = complete_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = complete_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = complete_table.find_element_by_xpath("tbody/tr[2]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = complete_table.find_element_by_xpath("tbody/tr[2]/td[14]")

        assert datatake.text == "N/A"

        start_msi = complete_table.find_element_by_xpath("tbody/tr[2]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = complete_table.find_element_by_xpath("tbody/tr[2]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

    def test_dhus_completeness_only_nppf_and_orbpre_and_rep_pass(self):

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

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/dhus-completeness")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "17600", stop_orbit = "17800", table_details = True, map = True, station_reports = True)

        # Check summary expected msi
        summary_expected_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-expected-msi")))

        assert summary_expected_msi

        assert summary_expected_msi.text == "33.033"

        # Check summary acquired msi
        summary_acquired_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-acquired-msi")))

        assert summary_acquired_msi

        assert summary_acquired_msi.text == "1.804"

        # Check summary processed to l1c msi
        summary_processed_l1c_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-processed-to-l1c-msi")))

        assert summary_processed_l1c_msi

        assert summary_processed_l1c_msi.text == "0.0"

        # Check summary processed to l2a msi
        summary_processed_l2a_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-processed-to-l2a-msi")))

        assert summary_processed_l2a_msi

        assert summary_processed_l2a_msi.text == "0.0"

        # Check summary generated to l1c tiles
        summary_generated_l1c_tiles = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-generated-l1c-tiles")))

        assert summary_generated_l1c_tiles

        assert summary_generated_l1c_tiles.text == "0"

        # Check summary generated to l2a tiles
        summary_generated_l2a_tiles = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-generated-l2a-tiles")))

        assert summary_generated_l2a_tiles

        assert summary_generated_l2a_tiles.text == "0"

        # Check summary missing acquistion
        summary_missing_acquistion = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-acquistion")))

        assert summary_missing_acquistion

        assert summary_missing_acquistion.text == "30.895"

        # Check summary missing processing l1c
        summary_missing_processing_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-processing-l1c")))

        assert summary_missing_processing_l1c

        assert summary_missing_processing_l1c.text == "32.699"

        # Check summary missing processing l2a
        summary_missing_processing_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-processing-l2a")))

        assert summary_missing_processing_l2a

        assert summary_missing_processing_l2a.text == "32.699"

        # Check number of elements in summary
        assert len(summary_expected_msi.find_elements_by_xpath("../../../div")) == 9

        # Check whether the map is displayed
        map_section = self.driver.find_element_by_id("dhus-completeness-on-map-section")

        condition = map_section.is_displayed()

        assert condition is True

        l1c_map_section = self.driver.find_element_by_id("dhus-completeness-l1c-on-map-section")

        condition = l1c_map_section.is_displayed()

        assert condition is True

        l2a_map_section = self.driver.find_element_by_id("dhus-completeness-l2a-on-map-section")

        condition = l2a_map_section.is_displayed()

        assert condition is True

        # Check whether the timeliness is displayed
        timeline_section = self.driver.find_element_by_id("dhus-completeness-e2e-timeline-section")

        condition = timeline_section.is_displayed()

        assert condition is True

        l1c_timeline_section = self.driver.find_element_by_id("dhus-completeness-l1c-e2e-timeline-section")

        condition = l1c_timeline_section.is_displayed()

        assert condition is True

        l2a_timeline_section = self.driver.find_element_by_id("dhus-completeness-l2a-e2e-timeline-section")

        condition = l2a_timeline_section.is_displayed()

        assert condition is True

        # Missing dissemination table
        missing_table = self.driver.find_element_by_id("dhus-completeness-list-table-MISSING")

        # Row 1
        level = missing_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert level.text == "L1C"

        satellite = missing_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert satellite.text == "S2A"

        orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip.text == "N/A"

        status = missing_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = missing_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = missing_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = missing_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = missing_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = missing_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = missing_table.find_element_by_xpath("tbody/tr[1]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = missing_table.find_element_by_xpath("tbody/tr[1]/td[14]")

        assert datatake.text == "N/A"

        start_msi = missing_table.find_element_by_xpath("tbody/tr[1]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = missing_table.find_element_by_xpath("tbody/tr[1]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 2
        level = missing_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L2A"

        satellite = missing_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert satellite.text == "S2A"

        orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip.text == "N/A"

        status = missing_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = missing_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = missing_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = missing_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = missing_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = missing_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = missing_table.find_element_by_xpath("tbody/tr[2]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = missing_table.find_element_by_xpath("tbody/tr[2]/td[14]")

        assert datatake.text == "N/A"

        start_msi = missing_table.find_element_by_xpath("tbody/tr[2]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = missing_table.find_element_by_xpath("tbody/tr[2]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Data availability table
        complete_table = self.driver.find_element_by_id("dhus-completeness-list-table-COMPLETE")

        # Row 1
        level = complete_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert level.text == "L1C"

        satellite = complete_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert satellite.text == "S2A"

        orbit = complete_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = complete_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = complete_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = complete_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip.text == "N/A"

        status = complete_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = complete_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = complete_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = complete_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = complete_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = complete_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = complete_table.find_element_by_xpath("tbody/tr[1]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = complete_table.find_element_by_xpath("tbody/tr[1]/td[14]")

        assert datatake.text == "N/A"

        start_msi = complete_table.find_element_by_xpath("tbody/tr[1]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = complete_table.find_element_by_xpath("tbody/tr[1]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 2
        level = complete_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L2A"

        satellite = complete_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert satellite.text == "S2A"

        orbit = complete_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = complete_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = complete_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = complete_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip.text == "N/A"

        status = complete_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = complete_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = complete_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = complete_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = complete_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = complete_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = complete_table.find_element_by_xpath("tbody/tr[2]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = complete_table.find_element_by_xpath("tbody/tr[2]/td[14]")

        assert datatake.text == "N/A"

        start_msi = complete_table.find_element_by_xpath("tbody/tr[2]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = complete_table.find_element_by_xpath("tbody/tr[2]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

    def test_dhus_completeness_without_l1b_and_l1c(self):

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

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPDAM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dam.ingestion_dam", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____MPS__20180721T110232_V20180721T085229_20180721T085414.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]
        
        filename = "S2__OPDHUS.xml"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dhus.ingestion_dhus", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "test_input_file_containing_dhus_publication_timings.xml"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_publication_dhus.ingestion_publication_dhus", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        wait = WebDriverWait(self.driver,5)

        self.driver.get("http://localhost:5000/views/dhus-completeness")

        functions.query(self.driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "17600", stop_orbit = "17800", table_details = True, map = True, station_reports = True)

        # Check summary expected msi
        summary_expected_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-expected-msi")))

        assert summary_expected_msi

        assert summary_expected_msi.text == "33.033"

        # Check summary acquired msi
        summary_acquired_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-acquired-msi")))

        assert summary_acquired_msi

        assert summary_acquired_msi.text == "1.804"

        # Check summary processed to l1c msi
        summary_processed_l1c_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-processed-to-l1c-msi")))

        assert summary_processed_l1c_msi

        assert summary_processed_l1c_msi.text == "1.833"

        # Check summary processed to l2a msi
        summary_processed_l2a_msi = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-processed-to-l2a-msi")))

        assert summary_processed_l2a_msi

        assert summary_processed_l2a_msi.text == "0.0"

        # Check summary generated to l1c tiles
        summary_generated_l1c_tiles = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-generated-l1c-tiles")))

        assert summary_generated_l1c_tiles

        assert summary_generated_l1c_tiles.text == "2"

        # Check summary generated to l2a tiles
        summary_generated_l2a_tiles = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-generated-l2a-tiles")))

        assert summary_generated_l2a_tiles

        assert summary_generated_l2a_tiles.text == "0"

        # Check summary missing acquistion
        summary_missing_acquistion = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-acquistion")))

        assert summary_missing_acquistion

        assert summary_missing_acquistion.text == "30.895"

        # Check summary missing processing l1c
        summary_missing_processing_l1c = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-processing-l1c")))

        assert summary_missing_processing_l1c

        assert summary_missing_processing_l1c.text == "30.866"

        # Check summary missing processing l2a
        summary_missing_processing_l2a = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-processing-l2a")))

        assert summary_missing_processing_l2a

        assert summary_missing_processing_l2a.text == "32.699"

        # Check summary missing l1c tiles in DHUS
        summary_missing_l1c_tiles_dhus = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-l1c-tiles-in-dhus")))

        assert summary_missing_l1c_tiles_dhus

        assert summary_missing_l1c_tiles_dhus.text == "1"

        # Check summary missing l1c tiles published in DHUS
        summary_missing_l1c_tiles_published_dhus = wait.until(EC.visibility_of_element_located((By.ID,"summary-dhus-completeness-missing-l1c-tiles-published-in-dhus")))

        assert summary_missing_l1c_tiles_published_dhus

        assert summary_missing_l1c_tiles_published_dhus.text == "1"

        # Check number of elements in summary
        assert len(summary_expected_msi.find_elements_by_xpath("../../../div")) == 11

        # Check whether the map is displayed
        map_section = self.driver.find_element_by_id("dhus-completeness-on-map-section")

        condition = map_section.is_displayed()

        assert condition is True

        l1c_map_section = self.driver.find_element_by_id("dhus-completeness-l1c-on-map-section")

        condition = l1c_map_section.is_displayed()

        assert condition is True

        l2a_map_section = self.driver.find_element_by_id("dhus-completeness-l2a-on-map-section")

        condition = l2a_map_section.is_displayed()

        assert condition is True

        # Check whether the timeliness is displayed
        timeline_section = self.driver.find_element_by_id("dhus-completeness-e2e-timeline-section")

        condition = timeline_section.is_displayed()

        assert condition is True

        l1c_timeline_section = self.driver.find_element_by_id("dhus-completeness-l1c-e2e-timeline-section")

        condition = l1c_timeline_section.is_displayed()

        assert condition is True

        l2a_timeline_section = self.driver.find_element_by_id("dhus-completeness-l2a-e2e-timeline-section")

        condition = l2a_timeline_section.is_displayed()

        assert condition is True

        # Missing dissemination table
        missing_table = self.driver.find_element_by_id("dhus-completeness-list-table-MISSING")

        # Row 1
        level = missing_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert level.text == "L1C"

        satellite = missing_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert satellite.text == "S2A"

        orbit = missing_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:54:19"

        stop_datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip.text == "N/A"

        status = missing_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = missing_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = missing_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = missing_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = missing_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = missing_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = missing_table.find_element_by_xpath("tbody/tr[1]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = missing_table.find_element_by_xpath("tbody/tr[1]/td[14]")

        assert datatake.text == "N/A"

        start_msi = missing_table.find_element_by_xpath("tbody/tr[1]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = missing_table.find_element_by_xpath("tbody/tr[1]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 2
        level = missing_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L1C"

        satellite = missing_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert satellite.text == "S2A"

        orbit = missing_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:52:29"

        stop_datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert stop_datastrip.text == "2018-07-21T08:54:19"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip.text == "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        status = missing_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert status.text == "MISSING DHUS DISSEMINATION"

        tiles = missing_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert tiles.text == "2"

        tiles_dam = missing_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert tiles_dam.text == "2"

        tiles_dhus = missing_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert tiles_dhus.text == "1"

        tiles_published_dhus = missing_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert tiles_published_dhus.text == "1"

        mean_time_dhus = missing_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert mean_time_dhus.text == "225.797"

        mean_time_dhus_publication = missing_table.find_element_by_xpath("tbody/tr[2]/td[13]")

        assert mean_time_dhus_publication.text == "1206891.184"

        datatake = missing_table.find_element_by_xpath("tbody/tr[2]/td[14]")

        assert datatake.text == "GS2A_20180721T083601_016077_N02.06"

        start_msi = missing_table.find_element_by_xpath("tbody/tr[2]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = missing_table.find_element_by_xpath("tbody/tr[2]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 3
        level = missing_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1C"

        satellite = missing_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert satellite.text == "S2A"

        orbit = missing_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = missing_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = missing_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert stop_datastrip.text == "2018-07-21T08:52:29"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip.text == "N/A"

        status = missing_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = missing_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = missing_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = missing_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = missing_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = missing_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = missing_table.find_element_by_xpath("tbody/tr[3]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = missing_table.find_element_by_xpath("tbody/tr[3]/td[14]")

        assert datatake.text == "N/A"

        start_msi = missing_table.find_element_by_xpath("tbody/tr[3]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = missing_table.find_element_by_xpath("tbody/tr[3]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 4
        level = missing_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L2A"

        satellite = missing_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert satellite.text == "S2A"

        orbit = missing_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = missing_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = missing_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = missing_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip.text == "N/A"

        status = missing_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = missing_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = missing_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = missing_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = missing_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = missing_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = missing_table.find_element_by_xpath("tbody/tr[4]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = missing_table.find_element_by_xpath("tbody/tr[4]/td[14]")

        assert datatake.text == "N/A"

        start_msi = missing_table.find_element_by_xpath("tbody/tr[4]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = missing_table.find_element_by_xpath("tbody/tr[4]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Data availability table
        complete_table = self.driver.find_element_by_id("dhus-completeness-list-table-COMPLETE")

        # Row 1
        level = complete_table.find_element_by_xpath("tbody/tr[1]/td[1]")

        assert level.text == "L1C"

        satellite = complete_table.find_element_by_xpath("tbody/tr[1]/td[2]")

        assert satellite.text == "S2A"

        orbit = complete_table.find_element_by_xpath("tbody/tr[1]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = complete_table.find_element_by_xpath("tbody/tr[1]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:54:19"

        stop_datastrip = complete_table.find_element_by_xpath("tbody/tr[1]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = complete_table.find_element_by_xpath("tbody/tr[1]/td[6]")

        assert datastrip.text == "N/A"

        status = complete_table.find_element_by_xpath("tbody/tr[1]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = complete_table.find_element_by_xpath("tbody/tr[1]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = complete_table.find_element_by_xpath("tbody/tr[1]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = complete_table.find_element_by_xpath("tbody/tr[1]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = complete_table.find_element_by_xpath("tbody/tr[1]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = complete_table.find_element_by_xpath("tbody/tr[1]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = complete_table.find_element_by_xpath("tbody/tr[1]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = complete_table.find_element_by_xpath("tbody/tr[1]/td[14]")

        assert datatake.text == "N/A"

        start_msi = complete_table.find_element_by_xpath("tbody/tr[1]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = complete_table.find_element_by_xpath("tbody/tr[1]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 2
        level = complete_table.find_element_by_xpath("tbody/tr[2]/td[1]")

        assert level.text == "L1C"

        satellite = complete_table.find_element_by_xpath("tbody/tr[2]/td[2]")

        assert satellite.text == "S2A"

        orbit = complete_table.find_element_by_xpath("tbody/tr[2]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = complete_table.find_element_by_xpath("tbody/tr[2]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:52:29"

        stop_datastrip = complete_table.find_element_by_xpath("tbody/tr[2]/td[5]")

        assert stop_datastrip.text == "2018-07-21T08:54:19"

        datastrip = complete_table.find_element_by_xpath("tbody/tr[2]/td[6]")

        assert datastrip.text == "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"

        status = complete_table.find_element_by_xpath("tbody/tr[2]/td[7]")

        assert status.text == "MISSING DHUS DISSEMINATION"

        tiles = complete_table.find_element_by_xpath("tbody/tr[2]/td[8]")

        assert tiles.text == "2"

        tiles_dam = complete_table.find_element_by_xpath("tbody/tr[2]/td[9]")

        assert tiles_dam.text == "2"

        tiles_dhus = complete_table.find_element_by_xpath("tbody/tr[2]/td[10]")

        assert tiles_dhus.text == "1"

        tiles_published_dhus = complete_table.find_element_by_xpath("tbody/tr[2]/td[11]")

        assert tiles_published_dhus.text == "1"

        mean_time_dhus = complete_table.find_element_by_xpath("tbody/tr[2]/td[12]")

        assert mean_time_dhus.text == "225.797"

        mean_time_dhus_publication = complete_table.find_element_by_xpath("tbody/tr[2]/td[13]")

        assert mean_time_dhus_publication.text == "1206891.184"

        datatake = complete_table.find_element_by_xpath("tbody/tr[2]/td[14]")

        assert datatake.text == "GS2A_20180721T083601_016077_N02.06"

        start_msi = complete_table.find_element_by_xpath("tbody/tr[2]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = complete_table.find_element_by_xpath("tbody/tr[2]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 3
        level = complete_table.find_element_by_xpath("tbody/tr[3]/td[1]")

        assert level.text == "L1C"

        satellite = complete_table.find_element_by_xpath("tbody/tr[3]/td[2]")

        assert satellite.text == "S2A"

        orbit = complete_table.find_element_by_xpath("tbody/tr[3]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = complete_table.find_element_by_xpath("tbody/tr[3]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = complete_table.find_element_by_xpath("tbody/tr[3]/td[5]")

        assert stop_datastrip.text == "2018-07-21T08:52:29"

        datastrip = complete_table.find_element_by_xpath("tbody/tr[3]/td[6]")

        assert datastrip.text == "N/A"

        status = complete_table.find_element_by_xpath("tbody/tr[3]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = complete_table.find_element_by_xpath("tbody/tr[3]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = complete_table.find_element_by_xpath("tbody/tr[3]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = complete_table.find_element_by_xpath("tbody/tr[3]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = complete_table.find_element_by_xpath("tbody/tr[3]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = complete_table.find_element_by_xpath("tbody/tr[3]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = complete_table.find_element_by_xpath("tbody/tr[3]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = complete_table.find_element_by_xpath("tbody/tr[3]/td[14]")

        assert datatake.text == "N/A"

        start_msi = complete_table.find_element_by_xpath("tbody/tr[3]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = complete_table.find_element_by_xpath("tbody/tr[3]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"

        # Row 4
        level = complete_table.find_element_by_xpath("tbody/tr[4]/td[1]")

        assert level.text == "L2A"

        satellite = complete_table.find_element_by_xpath("tbody/tr[4]/td[2]")

        assert satellite.text == "S2A"

        orbit = complete_table.find_element_by_xpath("tbody/tr[4]/td[3]")

        assert orbit.text == "16077"

        start_datastrip = complete_table.find_element_by_xpath("tbody/tr[4]/td[4]")

        assert start_datastrip.text == "2018-07-21T08:36:08.255634"

        stop_datastrip = complete_table.find_element_by_xpath("tbody/tr[4]/td[5]")

        assert stop_datastrip.text == "2018-07-21T09:08:50.195941"

        datastrip = complete_table.find_element_by_xpath("tbody/tr[4]/td[6]")

        assert datastrip.text == "N/A"

        status = complete_table.find_element_by_xpath("tbody/tr[4]/td[7]")

        assert status.text == "MISSING ACQUISITION"

        tiles = complete_table.find_element_by_xpath("tbody/tr[4]/td[8]")

        assert tiles.text == "N/A"

        tiles_dam = complete_table.find_element_by_xpath("tbody/tr[4]/td[9]")

        assert tiles_dam.text == "N/A"

        tiles_dhus = complete_table.find_element_by_xpath("tbody/tr[4]/td[10]")

        assert tiles_dhus.text == "N/A"

        tiles_published_dhus = complete_table.find_element_by_xpath("tbody/tr[4]/td[11]")

        assert tiles_published_dhus.text == "N/A"

        mean_time_dhus = complete_table.find_element_by_xpath("tbody/tr[4]/td[12]")

        assert mean_time_dhus.text == "N/A"

        mean_time_dhus_publication = complete_table.find_element_by_xpath("tbody/tr[4]/td[13]")

        assert mean_time_dhus_publication.text == "N/A"

        datatake = complete_table.find_element_by_xpath("tbody/tr[4]/td[14]")

        assert datatake.text == "N/A"

        start_msi = complete_table.find_element_by_xpath("tbody/tr[4]/td[15]")

        assert start_msi.text == "2018-07-21T08:35:58.255634"

        stop_msi = complete_table.find_element_by_xpath("tbody/tr[4]/td[16]")

        assert stop_msi.text == "2018-07-21T09:09:00.195941"