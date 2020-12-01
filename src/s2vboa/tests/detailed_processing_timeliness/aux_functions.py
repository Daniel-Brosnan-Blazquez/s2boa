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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import ActionChains,TouchActions
from selenium.webdriver.common.keys import Keys

def query(driver, wait, mission = None, start = None, stop = None, start_orbit = None, stop_orbit = None, table_details = True, map = True, station_reports = True):

    query_interface = driver.find_element_by_partial_link_text("Query interface")
    i = 0
    while not query_interface.get_attribute("aria-expanded") == "true":
        click(query_interface)
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

    if table_details is not True:
        # Click on show table_details
        click(driver.find_element_by_id("show-acquisition-table-details"))
    # end if

    if map is not True:
        # Click on show map
        click(driver.find_element_by_id("show-acquisition-map"))
    # end if

    if station_reports is not True:
        # Click on show station_reports
        click(driver.find_element_by_id("show-station-reports"))
    # end if

    click(driver.find_element_by_id("query-submit-button"))

def page_loaded(driver, wait, id):
    try:
        driver.find_element_by_id(id)
    except NoSuchElementException:
        return False
    return True

def click(element):

    done = False
    retries = 0
    while not done:
        try:
            element.click()
            done = True
        except ElementClickInterceptedException as e:
            if retries < 5:
                retries += 1
                pass
            else:
                raise e
            # end if
        # end try
    # end while
