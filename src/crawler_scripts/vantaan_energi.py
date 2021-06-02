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

def prepare_data(download_dir,facilityId,kind,unit):
    for f in os.listdir(download_dir):
        if kind == 'Heating':
            header = ['date','consumption','flow','supply-temp','return-temp','cooling','status','temp']
        else:
            header = ['date','consumption','other-consumption','winter-consumption','status','temp','inductive-power','capactive-reactive-power']
        df = pd.read_csv(os.path.join(download_dir,f),sep=';',names=header,skiprows=[0],encoding='latin-1')
        complete_data_block = []
        for i in range(len(df)):
            start_date = parse(df['date'][i],dayfirst=True)
            end_date = start_date + relativedelta(hours=1)
            if pd.notna(df['consumption'][i]):
                complete_data_block.append({'facilityId':facilityId,'kind':kind,'quantity':'ENERGY','startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['consumption'][i],'unit':unit})
            if pd.notna(df['temp'][i]):
                complete_data_block.append({'facilityId':facilityId,'kind':kind,'quantity':'TEMPERATURE','startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['temp'][i],'unit':'C'})
            # if kind == 'Heating':
            #     complete_data_block.append({'facilityId':facilityId,'kind':'Fjärrvärme','quantity':'VOLUME','startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['flow'][i],'unit':'m3'})
                
        os.remove(os.path.join(download_dir,f))
        return complete_data_block

def VantaanEnergi(agentRunContext):
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
            WebDriverWait(driver, 60).until(presence_of_element_located((By.ID,'nav-main')))
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
        
        driver.execute_script("document.getElementById('meteringPointSelector').style.display = 'inline';")

        time.sleep(2)

        #This is where the loop should be introduced

        facility_memo = {}

        facility_select_div = Select(driver.find_element_by_id('meteringPointSelector'))

        log.job(config.JOB_RUNNING_STATUS,'Started Scraping data')

        for option in facility_select_div.options:
            facility_memo[option.get_attribute('data-meteringpointcode')] = option.get_attribute('value')
        
        for key in facility_memo:

            driver.execute_script("window.location.href = '{0}'".format(facility_memo[key]))

            time.sleep(2)

            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'blockUI')))

            wait.until(presence_of_element_located((By.ID,'meteringPointSelector')))

            wait.until(EC.element_to_be_clickable((By.ID,'startDateSelector')))

            today_date = dt.now()
            start_date = today_date - relativedelta(months=12)

            driver.execute_script("document.getElementById('startDateSelector').value = '{0}';document.getElementById('updateInterval').click()".format("1.1.2011"))

            time.sleep(2)

            found = False

            while(not found):
                for entry in driver.get_log('browser'):
                    if entry['level'] == 'INFO' and "getCurrentViewInterval" in entry["message"] and entry["timestamp"] - int(time.time()*1000) <= 1:
                        found = True
                time.sleep(2)

            additional_data_div = driver.find_element_by_id("currentConsumption").text

            if 'kWh' in additional_data_div:
                unit = 'kWh'
            elif 'MWh' in additional_data_div:
                unit = 'MWh'
            
            # kind = driver.find_element_by_xpath('/html/body/div[4]/ul/li[{0}]'.format(index)).text.split('(')[1].replace(')','').stri

            kind = 'Electricity'
            
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'blockUI')))

            driver.execute_script('consumptionReportGraph.loadHourlyValues()')
            time.sleep(2)
            found = False

            while(not found):
                for entry in driver.get_log('browser'):
                    if entry['level'] == 'INFO' and "getCurrentViewInterval" in entry["message"] and entry["timestamp"] - int(time.time()*1000) <= 1:
                        found = True
                time.sleep(2)
            
            print('Now try selecting tunti')

            driver.execute_script("document.getElementById('navHourResolution').click();")

            time.sleep(2)

            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'blockUI')))

            driver.execute_script("document.getElementById('ExportToExcel').click();")

            time.sleep(2)

            has_downloaded = False
            download_sleep_count = 0

            while(not has_downloaded and download_sleep_count < 30):
                if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-3:] == 'csv' and download_sleep_count < 30 :
                    has_downloaded = True
                time.sleep(1)
                download_sleep_count += 1
            
            if download_sleep_count >= 30:
                log.info('Download failed for facility {0}'.format(facilityId))
                continue

            complete_data_block = prepare_data(download_dir,key,kind,unit)

            log.data(complete_data_block)

            log.info('Indexed data of facilityId {0}'.format(key))


        # /html/body/div[4]/ul/li[1]
        # /html/body/div[4]/ul/li[2]

        # index = 1

        # while(1):
        #     driver.find_element_by_id('s2id_meteringPointSelector').click()

        #     time.sleep(1)

        #     try:
        #         wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[4]/ul/li[{0}]'.format(index))))
        #     except TimeoutException:
        #         log.info('No more facilities available')
        #         break
            
        #     facilityId = driver.find_element_by_xpath('/html/body/div[4]/ul/li[{0}]'.format(index)).text.split()[0]
        #     kind = driver.find_element_by_xpath('/html/body/div[4]/ul/li[{0}]'.format(index)).text.split('(')[1].replace(')','').strip()

        #     driver.find_element_by_xpath('/html/body/div[4]/ul/li[{0}]'.format(index)).click()

        #     time.sleep(2)

        #     wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'blockUI')))

        #     time.sleep(2)

            # wait.until(EC.element_to_be_clickable((By.ID,'startDateSelector')))

            # today_date = dt.now()
            # start_date = today_date - relativedelta(months=12)

            # driver.execute_script("document.getElementById('startDateSelector').value = '{0}';document.getElementById('updateInterval').click()".format(dt.strftime(start_date, "%d.%m.%Y")))

            # time.sleep(2)

            # additional_data_div = driver.find_element_by_id("previousSimilarItem").find_element_by_class_name("panel-body").text

            # if 'kWh' in additional_data_div:
            #     unit = 'kWh'
            # elif 'MWh' in additional_data_div:
            #     unit = 'MWh'

            # wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'blockUI')))

            # driver.execute_script("document.getElementById('navHourResolution').click();")

            # time.sleep(2)

            # wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'blockUI')))

            # driver.execute_script("document.getElementById('ExportToExcel').click();")

            # time.sleep(2)

            # has_downloaded = False
            # download_sleep_count = 0

            # while(not has_downloaded):
            #     if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-3:] == 'csv' and download_sleep_count < 60 :
            #         has_downloaded = True
            #     time.sleep(1)
            #     download_sleep_count += 1
            
            # if download_sleep_count >= 60:
            #     log.info('Download failed for facility {0}'.format(facilityId))
            #     continue

            # complete_data_block = prepare_data(download_dir,facilityId,kind,unit)

            # log.data(complete_data_block)

            # log.info('Indexed data of facilityId {0}'.format(facilityId))

            # index += 1
        
        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,'Successfully scraped data for all available facilities')

    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())
        # driver.close()
        return
    
    # driver.close()
    os.rmdir(download_dir)