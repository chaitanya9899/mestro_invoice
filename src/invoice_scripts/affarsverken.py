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


def Affarsverken(agentRunContext):
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

        # to click on the Användarnamn username
        driver.find_element_by_id('Login1_UserName').send_keys(agentRunContext.requestBody['username'])

        # to click on the Lösenord password
        driver.find_element_by_id('Login1_Password').send_keys(agentRunContext.requestBody['password'])

        # to click on the loggi button
        wait.until( presence_of_element_located((By.XPATH, '/html/body/form/div[3]/div[2]/div[1]/table/tbody/tr/td/fieldset/input')))
        driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div[1]/table/tbody/tr/td/fieldset/input').click()

        time.sleep(2)
        # to select the EL button
        wait.until(presence_of_element_located((By.XPATH, '/html/body/div[1]/div[1]/form/div[6]/div/div/div[2]/div/div/ul/li[1]/a')))
        driver.find_element_by_xpath('/html/body/div[1]/div[1]/form/div[6]/div/div/div[2]/div/div/ul/li[1]/a').click()

        time.sleep(2)
        #  to select the Fakturor
        wait.until(presence_of_element_located((By.XPATH, '/html/body/div[1]/div[1]/form/div[6]/div/div/div[2]/div/div/ul/li[1]/ul/li[5]/a')))
        driver.find_element_by_xpath('/html/body/div[1]/div[1]/form/div[6]/div/div/div[2]/div/div/ul/li[1]/ul/li[5]/a').click()

        time.sleep(3)

        def Invoices():
            index = 1
            while 1:

                # to select the Arrow button to enter into the loop
                driver.find_element_by_xpath('/html/body/div[1]/div[1]/form/div[6]/div/div/div[1]/div[5]/div[1]/div[1]/a/div/b').click()

                # To select the search button
                time.sleep(2)
                driver.find_element_by_xpath('/html/body/div[1]/div[1]/form/div[6]/div/div/div[1]/div[5]/div[1]/div[1]/div/div/input').click()
                time.sleep(2)
                try:
                    time.sleep(1)
                    driver.find_element_by_xpath('/html/body/div[1]/div[1]/form/div[6]/div/div/div[1]/div[5]/div[1]/div[1]/div/ul/li[{0}]'.format(index)).click()

                except Exception as e:
                    time.sleep(3)
                    driver.find_element_by_xpath('/html/body/div[1]/div[1]/form/div[6]/div/div/div[1]/div[5]/div[1]/div[1]/div/div/input').click()
                    print(e)
                    break

                time.sleep(6)
                driver.execute_script('window.scrollTo(0,200);')
                time.sleep(6)
                countries = driver.find_elements_by_xpath('//table/tbody/tr')
                print(len(countries))
                time.sleep(3)
                print("no pop element")
                time.sleep(5)
                x = 100
                for i in range(1, len(countries)):
                    time.sleep(5)
                    x += 30
                    driver.execute_script(('window.scrollTo(0, {0});'.format(x)))
                    time.sleep(10)
                    pdf_link = driver.find_element_by_xpath("/html/body/div[1]/div[1]/form/div[6]/div/div/div[1]/div[7]/table/tbody/tr[" + str(i) + "]/td[5]/a")
                    print(pdf_link.text)
                    driver.execute_script("arguments[0].setAttribute('download','')", pdf_link)
                    print(i)
                    pdf_link.click()

                time.sleep(5)
                index += 1

        Invoices()

        def Bills():
            # to select the Arrow button to select year
            time.sleep(2)
            driver.find_element_by_xpath('/html/body/div[1]/div[1]/form/div[6]/div/div/div[1]/div[7]/div[2]/select').click()

            # to select the year button(2020)
            time.sleep(2)
            driver.find_element_by_xpath('/html/body/div[1]/div[1]/form/div[6]/div/div/div[1]/div[7]/div[2]/select/option[2]').click()

        Bills()
        Invoices()

        #  to select the Heat button
        time.sleep(2)
        driver.find_element_by_xpath('/html/body/div[1]/div[1]/form/div[6]/div/div/div[2]/div/div/ul/li[2]/a').click()

        #  to select the Fakturor(Bills)
        time.sleep(2)
        driver.find_element_by_xpath('/html/body/div[1]/div[1]/form/div[6]/div/div/div[2]/div/div/ul/li[2]/ul/li[4]/a').click()

        Invoices()

        # to select the year(2020) in heat
        Bills()
        Invoices()


    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS, str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())

    driver.close()
