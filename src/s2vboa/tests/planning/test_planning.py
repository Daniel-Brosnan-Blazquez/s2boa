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
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import ActionChains,TouchActions
from selenium.webdriver.common.keys import Keys

# Import engine of the DDBB
import eboa.engine.engine as eboa_engine
from eboa.engine.engine import Engine
from eboa.engine.query import Query
from eboa.datamodel.base import Session, engine, Base
from eboa.engine.errors import UndefinedEventLink, DuplicatedEventLinkRef, WrongPeriod, SourceAlreadyIngested, WrongValue, OddNumberOfCoordinates, EboaResourcesPathNotAvailable, WrongGeometry

# Import datamodel
from eboa.datamodel.dim_signatures import DimSignature
from eboa.datamodel.alerts import Alert
from eboa.datamodel.events import Event, EventLink, EventKey, EventText, EventDouble, EventObject, EventGeometry, EventBoolean, EventTimestamp
from eboa.datamodel.gauges import Gauge
from eboa.datamodel.sources import Source, SourceStatus
from eboa.datamodel.explicit_refs import ExplicitRef, ExplicitRefGrp, ExplicitRefLink
from eboa.datamodel.annotations import Annotation, AnnotationCnf, AnnotationText, AnnotationDouble, AnnotationObject, AnnotationGeometry, AnnotationBoolean, AnnotationTimestamp


class TestEngine(unittest.TestCase):
    def setUp(self):
        # Create the engine to manage the data
        self.engine_eboa = Engine()
        self.query_eboa = Query()

        # Create session to connect to the database
        self.session = Session()

        # Clear all tables before executing the test
        self.query_eboa.clear_db()

        self.options = Options()
        self.options.headless = True



    def tearDown(self):
        # Make sure the browser is closed
        subprocess.call(["pkill", "firefox"])

        # Close connections to the DDBB
        self.engine_eboa.close_session()
        self.query_eboa.close_session()
        self.session.close()

    def test_planning_no_data(self):

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        driver.get("http://localhost:5000/views/planning")

        # screenshot_path = os.path.dirname(os.path.abspath(__file__)) + "/screenshots/planning/"
        #
        # if not os.path.exists(screenshot_path):
        #     os.makedirs(screenshot_path)
        #
        # driver.save_screenshot(screenshot_path + "test.png")

        functions.query(driver, wait, "S2A", start = "2018-07-01T00:00:00", stop = "2018-07-31T23:59:59", start_orbit = "17600", stop_orbit = "17800", timeline = True, table_details = True, evolution = True, map = True)

        reporting = driver.find_element_by_xpath("/html/body/div[1]/div/div[3]/div")

        assert functions.is_empty(reporting) is True

        summary = driver.find_element_by_xpath("/html/body/div[1]/div/div[4]/div")

        assert functions.is_empty(summary) is True

        imaging = driver.find_element_by_xpath("/html/body/div[1]/div/div[5]/div")

        assert functions.is_empty(imaging) is True

        playback = driver.find_element_by_xpath("/html/body/div[1]/div/div[6]/div")

        assert functions.is_empty(playback) is True

        timeline = driver.find_element_by_xpath("/html/body/div[1]/div/div[7]/div")

        assert functions.is_empty(timeline) is True

        driver.quit
