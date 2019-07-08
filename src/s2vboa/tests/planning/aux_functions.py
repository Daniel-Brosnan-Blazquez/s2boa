"""
Extra functions used to perform selenium tests

Written by DEIMOS Space S.L. (femd)

module vboa
"""
import os
import sys
import unittest
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import ActionChains,TouchActions
from selenium.webdriver.common.keys import Keys


def query(driver, wait, mission = None, start = None, stop = None, start_orbit = None, stop_orbit = None, timeline = True, table_details = True, evolution = True, map = True):

    query_interface = driver.find_element_by_partial_link_text("Query interface")
    i = 0
    while not query_interface.get_attribute("aria-expanded") == "true":
        query_interface.click()
        # Add time to avoid lags on expanding the collapsed
        time.sleep(0.1)
    # end if

    # Extend mission selector and choose mission
    if mission is not None:
        mission_select = Select(driver.find_element_by_id("mission_static_query"))
        mission_select.select_by_visible_text(mission)

    if start is not None:
        # Select start date
        startTime = driver.find_element_by_id("start-input")
        ActionChains(driver).double_click(startTime).perform()
        startTime.send_keys(start)
    #   end if

    if stop is not None:
        # Select stop date
        stopTime = driver.find_element_by_id("stop-input")
        ActionChains(driver).double_click(stopTime).perform()
        stopTime.send_keys(stop)
    # end if

    if start_orbit is not None:
        driver.find_element_by_id("start-orbit").send_keys(start_orbit)
    # end if

    if stop_orbit is not None:
        driver.find_element_by_id("stop-orbit").send_keys(stop_orbit)
    # end if

    if timeline is not True:
        # Click on show timeline
        driver.find_element_by_id("show-planning-timeline").click()
    # end if

    if table_details is not True:
        # Click on show table_details
        driver.find_element_by_id("show-planning-table-details").click()
    # end if

    if evolution is not True:
        # Click on show evolution
        driver.find_element_by_id("show-planning-x-time-evolution").click()
    # end if

    if map is not True:
        # Click on show map
        driver.find_element_by_id("show-planning-map").click()
    # end if

    driver.find_element_by_id("query-submit-button").click()

def page_loaded(driver, wait, id):
    try:
        driver.find_element_by_id(id)
    except NoSuchElementException:
        return False
    return True
