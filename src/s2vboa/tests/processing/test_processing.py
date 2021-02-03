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

        # Check map complete segments tooltip
        # L0
        sad_data = self.query_eboa.get_events(gauge_names ={"filter": "SAD_DATA", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-20T22:00:21.024658", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T10:37:11.024915", "op": "=="}])
        isp_valididty = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:29.993268", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:18.226646", "op": "=="}])
        isp_valididty_processing_completeness_l0_1 = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0_CHANNEL_1", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:52:29", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T08:54:07", "op": "=="}])
        isp_valididty_processing_completeness_l0_2 = self.query_eboa.get_events(gauge_names ={"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0_CHANNEL_1", "op":"=="},
                                                                                start_filters =[{"date": "2018-07-21T08:54:07", "op":"=="}],
                                                                                stop_filters = [{"date": "2018-07-21T09:06:46", "op": "=="}])
        
        map_l0_complete_tooltip_info = [
            {
                "id": str(isp_valididty_processing_completeness_l0_1[0].event_uuid),
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l0_1[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr><tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                '<tr><td>Datastrip</td><td><a href="/eboa_nav/query-event-links/' + str(isp_valididty_processing_completeness_l0_1[0].event_uuid) + '">S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06</a></td></tr>' +
                '<tr><td>SAD coverage</td><td><a href="/eboa_nav/query-event-links/' + str(sad_data[0].event_uuid) + '">2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>' +
                "</table>",
                "geometries": [
                        {'value': 'POLYGON ((30.452534 27.975823, 30.393218 27.761953, 30.334101 27.548059, 30.27518 27.334141, 30.216437 27.120201, 30.157882 26.906237, 30.099518 26.69225, 30.041335 26.47824, 29.983323 26.264209, 29.925495 26.050155, 29.867847 25.836079, 29.810365 25.621982, 29.753053 25.407863, 29.695916 25.193723, 29.638949 24.979561, 29.582137 24.76538, 29.525493 24.551178, 29.469014 24.336955, 29.412691 24.122712, 29.356522 23.90845, 29.300513 23.694168, 29.244663 23.479866, 29.188953 23.265546, 29.133397 23.051206, 29.077993 22.836848, 29.022734 22.622471, 28.967615 22.408076, 28.912643 22.193662, 26.181532 22.774183, 26.232294 22.988981, 26.283157 23.203765, 26.334102 23.418538, 26.385137 23.633299, 26.436278 23.848045, 26.487527 24.062779, 26.538848 24.2775, 26.59028 24.492208, 26.641825 24.706901, 26.693467 24.921581, 26.745203 25.136248, 26.797057 25.3509, 26.849031 25.565537, 26.90109 25.780162, 26.953267 25.994771, 27.005569 26.209365, 27.057985 26.423945, 27.110499 26.63851, 27.163144 26.853059, 27.21592 27.067593, 27.268799 27.282112, 27.321801 27.496615, 27.374941 27.711102, 27.428213 27.925573, 27.481588 28.140029, 27.535107 28.354468, 27.58877 28.568889, 30.452534 27.975823))', 'name': 'footprint'},
                ],
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                }
            },
            {
                "id": str(isp_valididty_processing_completeness_l0_2[0].event_uuid),
                "tooltip": "<table border='1'>" + 
                "<tr><td>UUID</td><td>" + str(isp_valididty_processing_completeness_l0_2[0].event_uuid) + "</td></tr>" + 
                "<tr><td>Satellite</td><td>S2A</td></tr><tr>" + 
                "<tr><td>Downlink orbit</td><td>16078.0</td></tr>" +
                "<tr><td>Station</td><td>MPS_</td></tr>" +
                "<tr><td>Level</td><td>L0</td></tr>" +
                "<tr><td>Sensing orbit</td><td>16077</td></tr>" +
                "<tr><td>Status</td><td><a href='/views/specific-processing/" + str(isp_valididty[0].event_uuid) + "' class=bold-green>COMPLETE</a></td></tr>" +
                '<tr><td>Datastrip</td><td><a href="/eboa_nav/query-event-links/' + str(isp_valididty_processing_completeness_l0_2[0].event_uuid) + '">S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06</a></td></tr>' +
                '<tr><td>SAD coverage</td><td><a href="/eboa_nav/query-event-links/' + str(sad_data[0].event_uuid) + '">2018-07-20 22:00:21.024658_2018-07-21 10:37:11.024915</a></td></tr>' +
                "</table>",
                "geometries": [
                        {'value': 'POLYGON ((28.912643 22.193662, 28.855032 21.968334, 28.79757 21.742987, 28.740259 21.51762, 28.6831 21.292234, 28.626092 21.066829, 28.569226 20.841406, 28.512503 20.615965, 28.455924 20.390505, 28.399488 20.165027, 28.343189 19.939532, 28.287023 19.71402, 28.230994 19.48849, 28.175101 19.262944, 28.119338 19.037381, 28.063701 18.811801, 28.008195 18.586205, 27.952816 18.360593, 27.897562 18.134966, 27.842427 17.909322, 27.787415 17.683664, 27.732524 17.45799, 27.677752 17.232301, 27.623092 17.006598, 27.568548 16.78088, 27.514119 16.555148, 27.459803 16.329402, 27.405592 16.103642, 27.351491 15.877868, 27.297499 15.652081, 27.243613 15.426281, 27.189828 15.200468, 27.136146 14.974642, 27.082566 14.748804, 27.029086 14.522953, 26.975703 14.29709, 26.922415 14.071215, 26.869225 13.845329, 26.816129 13.619431, 26.763123 13.393521, 26.710208 13.167601, 26.657384 12.941669, 26.604649 12.715727, 26.552 12.489775, 26.499435 12.263812, 26.446956 12.037839, 26.394559 11.811856, 26.342244 11.585864, 26.290009 11.359862, 26.237852 11.13385, 26.185774 10.90783, 26.133772 10.681801, 26.081845 10.455763, 26.029991 10.229716, 25.978211 10.003662, 25.926501 9.777599, 25.874862 9.551527999999999, 25.823291 9.325449000000001, 25.771788 9.099363, 25.720351 8.87327, 25.66898 8.647169999999999, 25.617672 8.421061999999999, 25.566427 8.194948, 25.515244 7.968827, 25.464121 7.7427, 25.413058 7.516567, 25.362052 7.290428, 25.311102 7.064283, 25.26021 6.838132, 25.209372 6.611976, 25.158586 6.385815, 25.107852 6.159648, 25.057171 5.933477, 25.00654 5.707301, 24.955957 5.481121, 24.905421 5.254937, 24.854933 5.028748, 24.804491 4.802555, 24.754092 4.576359, 24.703736 4.350159, 24.653423 4.123956, 24.603152 3.897749, 24.55292 3.67154, 24.502726 3.445328, 24.45257 3.219113, 24.402454 2.992896, 24.352372 2.766676, 24.302323 2.540454, 24.252307 2.314231, 24.202327 2.088006, 24.152378 1.861779, 24.102456 1.635551, 24.052564 1.409321, 24.002704 1.183091, 23.95287 0.95686, 23.903059 0.7306280000000001, 23.853272 0.504396, 23.803516 0.278164, 23.75378 0.051931, 23.704065 -0.174301, 23.654367 -0.400533, 23.604696 -0.626765, 23.555043 -0.852996, 23.505405 -1.079226, 23.455781 -1.305456, 23.406179 -1.531684, 23.356591 -1.757911, 23.307014 -1.984136, 23.257447 -2.21036, 23.207897 -2.436581, 23.158358 -2.662801, 23.108827 -2.889019, 23.0593 -3.115234, 23.009785 -3.341447, 22.960279 -3.567656, 22.910775 -3.793863, 22.861273 -4.020067, 22.811777 -4.246268, 22.762287 -4.472465, 22.712795 -4.698659, 22.6633 -4.924848, 22.613806 -5.151034, 22.564316 -5.377216, 22.51482 -5.603393, 22.465316 -5.829566, 22.415807 -6.055735, 22.3663 -6.281898, 22.316783 -6.508057, 22.267253 -6.73421, 22.217713 -6.960358, 22.168172 -7.186501, 22.118617 -7.412637, 22.069045 -7.638768, 22.019457 -7.864894, 21.969866 -8.091011999999999, 21.920256 -8.317125000000001, 21.870625 -8.543231, 21.820972 -8.76933, 21.771313 -8.995422, 21.721631 -9.221508, 21.671924 -9.447585999999999, 21.622191 -9.673657, 21.572444 -9.89972, 21.522674 -10.125776, 21.472873 -10.351823, 21.423042 -10.577863, 21.373192 -10.803894, 21.323315 -11.029917, 21.273403 -11.255932, 21.223456 -11.481937, 21.173484 -11.707934, 21.123483 -11.933922, 21.073442 -12.159901, 21.023362 -12.38587, 20.973249 -12.61183, 20.923106 -12.837779, 20.872919 -13.063719, 20.822686 -13.289649, 20.772415 -13.515569, 20.722111 -13.741478, 20.671758 -13.967377, 20.621355 -14.193265, 20.570906 -14.419143, 20.520423 -14.645009, 20.469886 -14.870863, 20.419293 -15.096707, 20.368647 -15.322539, 20.317965 -15.548359, 20.267224 -15.774167, 20.216423 -15.999963, 20.165559 -16.225747, 20.114659 -16.451519, 20.063694 -16.677278, 20.012663 -16.903024, 19.961566 -17.128757, 19.910423 -17.354478, 19.859214 -17.580185, 19.807934 -17.805878, 19.756581 -18.031558, 19.705175 -18.257225, 19.653701 -18.482877, 19.60215 -18.708516, 19.55052 -18.93414, 19.49883 -19.159749, 19.447068 -19.385345, 19.395224 -19.610925, 19.343296 -19.836491, 19.291298 -20.062041, 19.239227 -20.287576, 19.187067 -20.513096, 19.134818 -20.7386, 19.082489 -20.964088, 19.030085 -21.189561, 18.977586 -21.415017, 18.924991 -21.640458, 18.872308 -21.865881, 18.819547 -22.091288, 18.766685 -22.316679, 18.71372 -22.542052, 18.660657 -22.767408, 15.908122 -22.182015, 15.96578 -21.957105, 16.023284 -21.732171, 16.080634 -21.507215, 16.137832 -21.282237, 16.194889 -21.057235, 16.251801 -20.832211, 16.308568 -20.607165, 16.36519 -20.382097, 16.421677 -20.157008, 16.478028 -19.931897, 16.53424 -19.706765, 16.590316 -19.481613, 16.646262 -19.256439, 16.70208 -19.031245, 16.757766 -18.806031, 16.813324 -18.580796, 16.868757 -18.355543, 16.92407 -18.130268, 16.979259 -17.904975, 17.034325 -17.679663, 17.089273 -17.454332, 17.144107 -17.228981, 17.198824 -17.003612, 17.253425 -16.778226, 17.307913 -16.552821, 17.362295 -16.327398, 17.416566 -16.101957, 17.470727 -15.876499, 17.524781 -15.651024, 17.578734 -15.425531, 17.632583 -15.200021, 17.686328 -14.974495, 17.739973 -14.748953, 17.793521 -14.523394, 17.846972 -14.297818, 17.900325 -14.072228, 17.953583 -13.846622, 18.00675 -13.621, 18.059825 -13.395362, 18.112809 -13.16971, 18.165703 -12.944043, 18.218511 -12.718361, 18.271233 -12.492665, 18.32387 -12.266954, 18.376422 -12.04123, 18.428893 -11.815492, 18.481283 -11.589739, 18.533593 -11.363974, 18.585824 -11.138195, 18.637979 -10.912403, 18.690058 -10.686598, 18.742063 -10.460781, 18.793994 -10.234951, 18.845854 -10.009109, 18.897642 -9.783253999999999, 18.949362 -9.557387, 19.001013 -9.33151, 19.052597 -9.10562, 19.104115 -8.879719, 19.155568 -8.653805999999999, 19.206959 -8.427883, 19.258287 -8.20195, 19.309554 -7.976005, 19.360761 -7.750049, 19.411909 -7.524084, 19.463001 -7.29811, 19.514035 -7.072124, 19.565015 -6.846129, 19.61594 -6.620125, 19.666814 -6.394112, 19.717634 -6.168088, 19.768404 -5.942056, 19.819126 -5.716016, 19.8698 -5.489968, 19.920424 -5.26391, 19.971003 -5.037844, 20.021537 -4.811771, 20.072029 -4.58569, 20.122477 -4.359601, 20.172882 -4.133504, 20.223247 -3.9074, 20.273575 -3.68129, 20.323862 -3.455172, 20.374111 -3.229048, 20.424325 -3.002917, 20.474506 -2.77678, 20.524651 -2.550636, 20.574761 -2.324486, 20.62484 -2.098331, 20.674891 -1.87217, 20.724911 -1.646004, 20.774899 -1.419832, 20.824861 -1.193655, 20.874799 -0.9674739999999999, 20.924711 -0.7412879999999999, 20.974594 -0.515096, 21.024455 -0.288901, 21.074296 -0.06270199999999999, 21.124118 0.163502, 21.173912 0.389709, 21.22369 0.6159210000000001, 21.273451 0.842135, 21.323198 1.068352, 21.372921 1.294574, 21.422632 1.520798, 21.47233 1.747025, 21.522018 1.973254, 21.571687 2.199486, 21.621347 2.425721, 21.670999 2.651957, 21.720645 2.878194, 21.770277 3.104434, 21.819902 3.330676, 21.869524 3.556918, 21.919144 3.783162, 21.968755 4.009407, 22.018362 4.235653, 22.067971 4.461899, 22.117582 4.688146, 22.16719 4.914393, 22.216795 5.140641, 22.266407 5.366888, 22.316025 5.593135, 22.365646 5.819382, 22.415267 6.045629, 22.464898 6.271874, 22.514541 6.498119, 22.564191 6.724362, 22.613844 6.950605, 22.663512 7.176846, 22.713195 7.403085, 22.762892 7.629322, 22.812594 7.855558, 22.862315 8.081792, 22.912056 8.308023, 22.961817 8.534250999999999, 23.011584 8.760477, 23.061375 8.986701, 23.111191 9.212921, 23.161033 9.439138, 23.210884 9.665352, 23.260763 9.891563, 23.310671 10.117769, 23.360609 10.343972, 23.410563 10.570171, 23.460547 10.796366, 23.510565 11.022556, 23.560617 11.248742, 23.610692 11.474923, 23.660799 11.7011, 23.710944 11.927271, 23.761129 12.153436, 23.811342 12.379597, 23.86159 12.605752, 23.91188 12.831902, 23.962216 13.058045, 24.012587 13.284182, 24.062994 13.510314, 24.113449 13.736438, 24.163954 13.962556, 24.214501 14.188667, 24.265086 14.414772, 24.315725 14.64087, 24.366418 14.866959, 24.417161 15.093042, 24.467944 15.319117, 24.518785 15.545184, 24.569686 15.771243, 24.620645 15.997294, 24.671645 16.223337, 24.722709 16.449372, 24.773838 16.675397, 24.825033 16.901414, 24.876271 17.127422, 24.927579 17.353421, 24.978956 17.57941, 25.030407 17.805389, 25.081905 18.03136, 25.133477 18.25732, 25.185125 18.48327, 25.236851 18.70921, 25.288633 18.93514, 25.340491 19.161059, 25.392431 19.386967, 25.444454 19.612864, 25.496543 19.83875, 25.548709 20.064626, 25.600964 20.290489, 25.653308 20.516341, 25.705726 20.742181, 25.758225 20.968009, 25.810817 21.193826, 25.863506 21.419629, 25.916278 21.64542, 25.969133 21.871199, 26.022088 22.096965, 26.075146 22.322717, 26.128296 22.548456, 26.181532 22.774183, 28.912643 22.193662))', 'name': 'footprint'},
                ],
                "style": {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                }
            },
        ]

        returned_processing_geometries_complete_l0 = self.driver.execute_script('return processing_geometries_complete_l0;')
        assert map_l0_complete_tooltip_info == returned_processing_geometries_complete_l0
