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

def prepare_data(download_dir,facilityId):
    for f in os.listdir(download_dir):
        header = ['date','consumption','flow','supply-temp','return-temp','cooling','status','temp']
        df = pd.read_csv(os.path.join(download_dir,f),sep=';',names=header,skiprows=[0])
        complete_data_block = []
        for i in range(len(df)):
            start_date = parse(df['date'][i],dayfirst=True)
            end_date = start_date + relativedelta(hours=1)
            complete_data_block.append({'facilityId':facilityId,'kind':'Fjärrvärme','quantity':'ENERGY','startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['consumption'][i],'unit':'MWh'})
            complete_data_block.append({'facilityId':facilityId,'kind':'Fjärrvärme','quantity':'VOLUME','startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['flow'][i],'unit':'m3'})
            complete_data_block.append({'facilityId':facilityId,'kind':'Fjärrvärme','quantity':'TEMPERATURE','startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['temp'][i],'unit':'C'})
        os.remove(os.path.join(download_dir,f))
        return complete_data_block

def Nevel(agentRunContext):
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

        wait.until(presence_of_element_located((By.ID,'emailfield')))
        driver.execute_script("document.getElementById('emailfield').value='{0}';document.getElementById('Password').value='{1}';document.getElementById('loginsubmit').click();".format(agentRunContext.requestBody['username'],agentRunContext.requestBody['password']))

        try:
            WebDriverWait(driver, 15).until(presence_of_element_located((By.ID,'userMenu')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to login, invalid username or password')
            driver.close()
            os.rmdir(download_dir)
            return
        
        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')
        
        driver.execute_script("window.location.href = '/Reporting/CustomerConsumption';")

        try:
            wait.until(presence_of_element_located((By.ID,'meteringPointSelector')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS, "Not loading consumption details")
            log.info('The website does not load consumption details for this user with wait of 100 second')
            driver.close()
            os.rmdir(download_dir)
            return

        #This is where the loop should be introduced

        facility_select = Select(driver.find_element_by_id('meteringPointSelector'))

        options = facility_select.options

        for i in range(len(options)):

            facility_select = Select(driver.find_element_by_id('meteringPointSelector'))

            facility_select.select_by_index(i)

            time.sleep(2)

            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'blockUI')))

            time.sleep(2)

            facility_select = Select(driver.find_element_by_id('meteringPointSelector'))

            facilityId = facility_select.options[i].get_attribute('data-meteringpointcode')

            wait.until(presence_of_element_located((By.ID,'startDateSelector')))
        
            today_date = dt.now()
            start_date = today_date - relativedelta(months=12)

            driver.execute_script("document.getElementById('startDateSelector').value = '{0}';document.getElementById('updateInterval').click()".format(dt.strftime(start_date, "%d.%m.%Y")))

            time.sleep(2)

            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'blockUI')))

            driver.execute_script("document.getElementById('navHourResolution').click();")

            time.sleep(2)

            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'blockUI')))

            driver.execute_script("document.getElementById('ExportToExcel').click();")

            time.sleep(2)

            has_downloaded = False
            download_sleep_count = 0

            while(not has_downloaded and download_sleep_count < 25):
                if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-3:] == 'csv' and download_sleep_count < 60 :
                    has_downloaded = True
                time.sleep(1)
                download_sleep_count += 1
            
            if download_sleep_count >= 60:
                log.info('Download failed for facility {0}'.format(facilityId))
                continue

            complete_data_block = prepare_data(download_dir,facilityId)

            log.data(complete_data_block)

            log.info('Indexed data of facilityId {0}'.format(facilityId))
        
        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,'Successfully scraped data for all available facilities')

    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        driver.close()
        return
    
    driver.close()
    os.rmdir(download_dir)