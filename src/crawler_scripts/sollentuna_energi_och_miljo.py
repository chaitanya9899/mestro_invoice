from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException,TimeoutException,JavascriptException,StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC

import os
import pandas as pd
import time
import traceback
import threading

from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse


from common import get_driver
from common import Log
import config

def SollentunaEnergiOchMiljo(agentRunContext):
    
    log = Log(agentRunContext)

    try:
        log.job(config.JOB_RUNNING_STATUS,'{0} thread started execution'.format(agentRunContext.requestBody['agentId']))

        thread_id = str(threading.get_ident())
        download_dir = os.path.join(os.getcwd(),'temp','temp-'+thread_id)

        log.info('{0} with threadID {1} has its temp directory in {2}'.format(agentRunContext.requestBody['agentId'],thread_id,download_dir))

        driver = get_driver(download_dir)
        driver.maximize_window()
        driver.get(agentRunContext.homeURL)

        wait = WebDriverWait(driver,100)

        try:
            wait.until(EC.element_to_be_clickable((By.ID,'UserName')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Not able to load the website')
            log.info('Timeout exception caused by waiting for the username input to load')
            driver.close()
            os.rmdir(download_dir)
            return

        driver.execute_script("document.getElementById('UserName').value = '{0}';document.getElementById('Password').value = '{1}';document.getElementById('LoginButton').click();".format(agentRunContext.requestBody['username'],agentRunContext.requestBody['password']))

        try:
            wait.until(EC.element_to_be_clickable((By.ID,'mainMenu')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to login, invalid username or password')
            log.info('Timeout exception caused by waiting for mainMenu div to load')
            driver.close()
            os.rmdir(download_dir)
            return

        driver.execute_script('window.location.href = "/emtredirect.aspx"')

        try:
            wait.until(EC.visibility_of_element_located((By.ID,'header')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Not able to load website')
            log.info('Timeout exception caused by waiting for header div to load')
            driver.close()
            os.rmdir(download_dir)
            return
        
        driver.execute_script('window.location.href = "/SiteGroup/RawDataExport.aspx"')

        try:
            wait.until(EC.visibility_of_element_located((By.ID,'MainContent_tvCustomTreeView_pnlTreeview')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Not able to load website')
            log.info('Timeout exception caused by waiting for MainContent_tvCustomTreeView_pnlTreeview div to load')
            driver.close()
            os.rmdir(download_dir)
            return

        total_fac_div = driver.find_element_by_id('MainContent_tvCustomTreeView_tvCustomTreeView')

        facilities = total_fac_div.find_elements_by_tag_name('table')

        for facility in facilities:
            if r'sC\\Z||' in facility.find_element_by_tag_name('a').get_attribute('href'):
                facility.click()

                time.sleep(3)

                driver.refresh()

                
        



        

    except Exception as e:
        print(traceback.format_exc())
        log.exception(traceback.format_exc())
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))

    # driver.close()
    os.rmdir(download_dir)