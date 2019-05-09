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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import ActionChains,TouchActions
from selenium.webdriver.common.keys import Keys


def query(driver, wait, mission, start = None, stop = None, start_orbit = None, stop_orbit = None, timeline = True, table_details = True, evolution = True, map = True):

    missions = {"S2_": "1", "S2A": "2", "S2B": 3}

    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/form/div/div[1]/h3/a").click()

    # Extend mission selector and choose mission
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/form/div/div[2]/div[1]/div/select").click()
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/form/div/div[2]/div[1]/div/select/option[" + missions[mission] + "]").click()

    if start is not None:
        # Select start date
        startTime = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/form/div/div[2]/div[2]/div[1]/div/input")
        ActionChains(driver).double_click(startTime).perform()
        startTime.send_keys(start)
    #   end if

    if stop is not None:
        # Select stop date
        stopTime = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/form/div/div[2]/div[2]/div[2]/div/input")
        ActionChains(driver).double_click(stopTime).perform()
        stopTime.send_keys(stop)
    # end if

    if start_orbit is not None:
        driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/form/div/div[2]/div[3]/div[1]/div/input").send_keys(start_orbit)
    # end if

    if start_orbit is not None:
        driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/form/div/div[2]/div[3]/div[2]/div/input").send_keys(stop_orbit)
    # end if

    if timeline is not True:
        # Click on show timeline
        driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/form/div/div[2]/div[5]/label").click()
    # end if

    if table_details is not True:
        # Click on show table_details
        driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/form/div/div[2]/div[6]/label").click()
    # end if

    if evolution is not True:
        # Click on show evolution
        driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/form/div/div[2]/div[7]/label").click()
    # end if

    if map is not True:
        # Click on show map
        driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/form/div/div[2]/div[8]/label").click()
    # end if

    driver.save_screenshot("query.png")
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/form/div/div[2]/div[4]/button").click()

def is_empty(section):
    texts = ["There is no information for setting the orbit period.",
             "There are no imaging operations during the requested period.",
             "There are no playback operations during the requested period.",
             "There are no planning events during the requested period."]
    try:
        ret_text = section.find_element_by_xpath("/html/body/div[1]/div/div[4]/div/div[2]/p").text
    except NoSuchElementException:
        return False
    if [ret_text == text for text in texts]:
        return True
    else:
        return False
