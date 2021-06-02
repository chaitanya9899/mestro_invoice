from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException,TimeoutException,JavascriptException,StaleElementReferenceException
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

def VattenfallHeating(agentRunContext):
    print(agentRunContext.homeURL)
    log = Log(agentRunContext)

    try:
        log.job(config.JOB_RUNNING_STATUS,'{0} thread started execution'.format(agentRunContext.requestBody['agentId']))
        thread_id = str(threading.get_ident())
        download_dir = os.path.join(os.getcwd(),'temp','temp-'+thread_id)
        print(download_dir)
        log.info('{0} with threadID {1} has its temp directory in {2}'.format(agentRunContext.requestBody['agentId'],thread_id,download_dir))
        driver = get_driver(download_dir)
        driver.maximize_window()
        driver.get(agentRunContext.homeURL)
        wait = WebDriverWait(driver, 100)

        

        # to open the Loggin button
        wait.until(presence_of_element_located((By.XPATH, '/html/body/app-root/div/app-home/div/div/div/a[3]')))
        driver.find_element_by_xpath('/html/body/app-root/div/app-home/div/div/div/a[3]').click()

        # to enter the username
        driver.find_element_by_id('usernameInput').send_keys(agentRunContext.requestBody['username'])

        # to enter the password
        driver.find_element_by_id("password").send_keys(agentRunContext.requestBody['password'])

        # to press the login buttom
        driver.find_element_by_xpath('/html/body/div[1]/div/div[3]/div/div/form/div[2]').click()

        # to select the Faktour
        time.sleep(3)
        wait.until(presence_of_element_located((By.XPATH, '/html/body/app-root/div/app-landing/div/div/app-left-navigation/aside/ul/li[6]')))
        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')
        driver.find_element_by_xpath('/html/body/app-root/div/app-landing/div/div/app-left-navigation/aside/ul/li[6]').click()


        time.sleep(3)

        # to select the toggle button
        wait.until(presence_of_element_located((By.XPATH, '/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/mat-card/app-year-picker/mat-form-field/div/div[1]/div[2]/mat-datepicker-toggle/button')))
        driver.find_element_by_xpath('/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/mat-card/app-year-picker/mat-form-field/div/div[1]/div[2]/mat-datepicker-toggle/button').click()
        # driver.find_element_by_xpath('/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/mat-card/app-year-picker/mat-form-field/div/div[1]/div[1]/input').send_keys(2020)

        # to select the year (2017)
        driver.find_element_by_xpath('/html/body/div[3]/div[2]/div/mat-datepicker-content/div[2]/mat-calendar/div/mat-multi-year-view/table/tbody/tr[5]/td[4]/div[1]').click()

        def MI():
            time.sleep(3)
            # to select the Arrow button (Objekt per sida)
            driver.find_element_by_xpath('/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/mat-card/div/div/div/app-invoice-table/div[2]/mat-paginator/div/div/div[1]/mat-form-field/div/div[1]/div/mat-select/div/div[2]/div').click()
            time.sleep(3)
            # to select the minimum numbers button (25)(Objekt per sida)
            driver.find_element_by_xpath('/html/body/div[3]/div[2]/div/div/div/mat-option[3]/span').click()
            index = 1

            while (1):
                # To select the search button
                driver.find_element_by_xpath('/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/div/app-search-invoice/form/mat-form-field/div/div[1]/div[2]/input').click()
                # /html/body/div[2]/div[1]/div/button
                time.sleep(3)
                try:
                    driver.find_element_by_xpath( 'html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/mat-card/div/div/div/app-invoice-table/div[1]/table/tbody/tr[{0}]'.format(index)).click()

                except Exception as e:
                    driver.find_element_by_xpath('/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/div/app-search-invoice/form/mat-form-field/div/div[1]/div[2]/input').click()
                    print(e)
                    break


                time.sleep(3)

                # to select the download button
                driver.find_element_by_class_name("text-right").click()

                index += 1
        MI()

        # to select the toggle button
        wait.until(presence_of_element_located((By.XPATH, '/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/mat-card/app-year-picker/mat-form-field/div/div[1]/div[2]/mat-datepicker-toggle/button')))
        driver.find_element_by_xpath('/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/mat-card/app-year-picker/mat-form-field/div/div[1]/div[2]/mat-datepicker-toggle/button').click()

        log.job(config.JOB_RUNNING_STATUS,'Started downloading invoices')

        # to select the year (2018)
        driver.find_element_by_xpath('/html/body/div[3]/div[2]/div/mat-datepicker-content/div[2]/mat-calendar/div/mat-multi-year-view/table/tbody/tr[6]/td[1]').click()

        MI()

        # to select the toggle button
        wait.until(presence_of_element_located((By.XPATH, '/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/mat-card/app-year-picker/mat-form-field/div/div[1]/div[2]/mat-datepicker-toggle/button')))
        driver.find_element_by_xpath('/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/mat-card/app-year-picker/mat-form-field/div/div[1]/div[2]/mat-datepicker-toggle/button').click()

        # to select the year (2019)
        driver.find_element_by_xpath('/html/body/div[3]/div[2]/div/mat-datepicker-content/div[2]/mat-calendar/div/mat-multi-year-view/table/tbody/tr[6]/td[2]').click()

        MI()


        # to select the toggle button
        wait.until(presence_of_element_located((By.XPATH, '/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/mat-card/app-year-picker/mat-form-field/div/div[1]/div[2]/mat-datepicker-toggle/button')))
        driver.find_element_by_xpath('/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/mat-card/app-year-picker/mat-form-field/div/div[1]/div[2]/mat-datepicker-toggle/button').click()

        # to select the year (2020)
        driver.find_element_by_xpath('/html/body/div[3]/div[2]/div/mat-datepicker-content/div[2]/mat-calendar/div/mat-multi-year-view/table/tbody/tr[6]/td[3]').click()

        MI()


        # to select the toggle button
        wait.until(presence_of_element_located((By.XPATH, '/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/mat-card/app-year-picker/mat-form-field/div/div[1]/div[2]/mat-datepicker-toggle/button')))
        driver.find_element_by_xpath('/html/body/app-root/div/app-landing/div/mat-drawer-container/mat-drawer-content/app-invoices/div/mat-card/app-year-picker/mat-form-field/div/div[1]/div[2]/mat-datepicker-toggle/button').click()

        # to select the year (2021)
        driver.find_element_by_xpath('/html/body/div[3]/div[2]/div/mat-datepicker-content/div[2]/mat-calendar/div/mat-multi-year-view/table/tbody/tr[6]/td[4]').click()

        MI()
        
    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())
    
    driver.close()
    os.rmdir(download_dir)