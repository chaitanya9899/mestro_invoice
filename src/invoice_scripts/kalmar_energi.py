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

def KalmarEnergi(agentRunContext):
    
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
        driver.find_element_by_xpath('/html/body/form/div[4]/div/div[2]/div[3]/div/div[1]/div[2]/div/ul/li[2]').click()
        time.sleep(2)
        # to click on the Användarnamn username
        driver.find_element_by_id('txtUser').send_keys(agentRunContext.requestBody['username'])
        # to click on the Lösenord password
        driver.find_element_by_id('txtPassword').send_keys(agentRunContext.requestBody['password'])
        # to click on the loggi button
        wait.until(presence_of_element_located((By.XPATH, '/html/body/form/div[4]/div/div[2]/div[3]/div/div[1]/div[2]/div/div[2]/div[4]/div/div[1]/div/input')))
        driver.find_element_by_xpath('/html/body/form/div[4]/div/div[2]/div[3]/div/div[1]/div[2]/div/div[2]/div[4]/div/div[1]/div/input').click()
        # to select the Fakturor(Bills) button
        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')

        wait.until(presence_of_element_located((By.XPATH, '/html/body/form/nav/div[2]/ul/li[3]/a')))
        driver.find_element_by_xpath('/html/body/form/nav/div[2]/ul/li[3]/a').click()
        time.sleep(2)
        # to select the search button

        driver.execute_script(('window.scrollTo(0,200);'))
        time.sleep(3)
        # driver.find_element_by_xpath("/html/body/form/div[3]/div/div[2]/div[2]/div[5]/div/div/button").click()
        # time.sleep(2)

        # driver.find_element_by_xpath('/html/body/form/div[3]/div/div[2]/div[2]/div[5]/div/ul/li/div/div/input').send_keys('Betald')
        # time.sleep(2)
        # driver.find_element_by_xpath("/html/body/form/div[3]/div/div[2]/div[2]/div[5]/div/ul/li/div/button[1]").click()



        table=driver.find_elements_by_xpath('//tbody/tr/td[7]')
        print(len(table))
        time.sleep(3)
        try:
            driver.find_element_by_class_name("notification-close").click()
        except:
            print("no pop element")
        x=100
        time.sleep(5)
        log.job(config.JOB_RUNNING_STATUS,'Started downloading invoices')



        for i in range(1,len(table)):
            time.sleep(5)
            x+=30
            driver.execute_script(('window.scrollTo(0, {0});'.format(x)))
            time.sleep(10)
            pdf_link=driver.find_element_by_xpath("/html/body/form/div[3]/div/div[2]/div[2]/table/tbody/tr["+str(i)+"]/td[7]/a")
            betlad=driver.find_element_by_xpath("/html/body/form/div[3]/div/div[2]/div[2]/table/tbody/tr["+str(i)+"]/td[1]")
            print(betlad.text)
            print(pdf_link.text)
            if betlad.text=='Betald':
                driver.execute_script("arguments[0].setAttribute('download','')",pdf_link)
                time.sleep(2)
                pdf_link.click()
                print(i)
                time.sleep(5)


    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())
    
    driver.close()
    os.rmdir(download_dir)
