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
from calendar import monthrange


from common import get_driver
from common import Log
import config

def GoteborgEnergi(agentRunContext):
    
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

        try:
            wait.until(EC.element_to_be_clickable((By.ID,'username')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Not able to load the website')
            driver.close()
            os.rmdir(download_dir)
            return
        
        driver.execute_script("document.getElementById('username').value = '{0}';document.getElementById('password').value = '{1}';document.getElementsByClassName('login-buttons')[0].getElementsByTagName('button')[0].click();".format(agentRunContext.requestBody['username'],agentRunContext.requestBody['password']))

        try:
            wait.until(EC.element_to_be_clickable((By.CLASS_NAME,"ge-desktop-navigation__user-col")))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS, "Unable to login, invalid username or password")
            driver.close()
            os.rmdir(download_dir)
            return
        
        user_select = driver.find_element_by_class_name("ge-desktop-navigation__user-col")
        user_select.find_element_by_tag_name('a').click()

        time.sleep(2)

        wait.until(EC.element_to_be_clickable((By.CLASS_NAME,"css-2b097c-container")))

        time.sleep(2)

        driver.find_element_by_class_name("css-2b097c-container").click()

        time.sleep(2)

        driver.execute_script("console.log(document.getElementsByClassName('css-1laao21-a11yText'));")


    
    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())
    
    # driver.close()
    # os.rmdir(download_dir)