from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException, JavascriptException, \
    StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

import os
import pandas as pd
import time
import traceback
import threading
from openpyxl import load_workbook
from calendar import monthrange

from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from calendar import monthrange

from common import get_driver
from common import Log
import config


def SolorBioenergi(agentRunContext):
    log = Log(agentRunContext)

    try:
        log.job(config.JOB_RUNNING_STATUS,
                '{0} thread started execution'.format(agentRunContext.requestBody['agentId']))
        thread_id = str(threading.get_ident())
        download_dir = os.path.join(os.getcwd(), 'temp', 'temp-' + thread_id)
        print(download_dir)
        log.info('{0} with threadID {1} has its temp directory in {2}'.format(agentRunContext.requestBody['agentId'],
                                                                              thread_id, download_dir))
        driver = get_driver(download_dir)
        driver.maximize_window()
        driver.get(agentRunContext.homeURL)
        wait = WebDriverWait(driver, 100)

        wait = WebDriverWait(driver, 10)

        # to click on the Användarnamn username
        driver.find_element_by_id('MainContent_Email').send_keys(agentRunContext.requestBody['username'])

        # to click on the Lösenord password
        driver.find_element_by_id('MainContent_Password').send_keys(agentRunContext.requestBody['password'])

        # to click on the loggi button
        wait.until(presence_of_element_located((By.XPATH, '/html/body/form/div[4]/div[2]/div[1]/section/div/div[4]/div/input')))
        driver.find_element_by_xpath('/html/body/form/div[4]/div[2]/div[1]/section/div/div[4]/div/input').click()

        # to select the city
        wait.until(presence_of_element_located((By.XPATH, '/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[1]/tbody/tr/td[2]/select')))
        city = Select(driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[1]/tbody/tr/td[2]/select'))
        city.select_by_visible_text(agentRunContext.requestBody['city'])
        time.sleep(2)

        wait.until(presence_of_element_located((By.XPATH, '/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[1]/tbody/tr/td[2]/select')))
        city = Select(driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[1]/tbody/tr/td[2]/select'))
        city.select_by_visible_text(agentRunContext.requestBody['city'])

        # to click on the Kundnummer(number)
        driver.find_element_by_id('ContentPlaceHolder1_tbxKundnummer').send_keys(agentRunContext.requestBody['customerNumber'])

        # to click on the Person-/Org.-nummer YYMMDDABCD(number)
        driver.find_element_by_id('ContentPlaceHolder1_tbxIdNummer').send_keys(agentRunContext.requestBody['orgNumber'])

        # to click on the Hamta data(Download Data) button
        wait.until(presence_of_element_located((By.XPATH, '/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[1]/tbody/tr/td[7]/input')))
        driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[1]/tbody/tr/td[7]/input').click()

        def solor():
            # to download the invoice of 25103092711 and 25103092810 file
            driver.find_element_by_id('ContentPlaceHolder1_GridView2_btnPDFFileName_0').click()

            # to download the invoice of 25103054513 and 25103054612 file
            driver.find_element_by_id('ContentPlaceHolder1_GridView2_btnPDFFileName_1').click()

            # to download the invoice of 25103024110 and 25103024219 file
            driver.find_element_by_id('ContentPlaceHolder1_GridView2_btnPDFFileName_2').click()

            # to download the invoice of 25102978217 and 25102978316 file
            driver.find_element_by_id('ContentPlaceHolder1_GridView2_btnPDFFileName_3').click()

            # to download the invoice of 25102939912 and 25102940019 file
            driver.find_element_by_id('ContentPlaceHolder1_GridView2_btnPDFFileName_4').click()

            # to download the invoice of 25102901714 and 25102901813 file
            driver.find_element_by_id('ContentPlaceHolder1_GridView2_btnPDFFileName_5').click()

        solor()

        time.sleep(6)
        # to select the Arrow
        driver.find_element_by_id('ContentPlaceHolder1_ddlValjAnlaggning').click()

        # to select the Another number
        driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[2]/tbody/tr[4]/td[2]/select/option[2]').click()

        solor()

        # agentRunContext.requestBody['username']
        # agentRunContext.requestBody['password']

    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS, str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())

    driver.close()
    # os.rmdir(download_dir)
