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

def prepare_data(download_dir):
    for f in os.listdir(download_dir):
        df = pd.read_csv(os.path.join(download_dir,f),sep=';',names=['facilityId','date','type','total-energy-reading','monthly-energy-consumption','energy-unit','sep-1','total-volume-reading','monthly-volume-consumption','sep-2','time-counter','time-consumption','time-unit','sep-3','akk-flow','akk-return','akk-unit','sep-4','avg-forward-temp','avg-return-temp','cooling','sep-5','expected-return-temp','upper-border-temp','lower-border-temp','sep-6','code','error-code','sep-7','sep-8','additional'],skiprows=[0,1,2,3,4,5,6,7,8,9,10,11],encoding='utf-8')

        complete_data_block = []

        for i in range(len(df)):
            if df['type'][i] == 'Mellemafl.':
                end_date = dt.strptime(df['date'][i],"%d-%m-%Y")
                start_date = end_date - relativedelta(hours=float(str(df['time-consumption'][i]).replace(',','.')))
                complete_data_block.append({'facilityId':df['facilityId'][i],'startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'quantity':'ENERGY','kind':'Fjärrvärme','value':df['monthly-energy-consumption'][i],'unit':df['energy-unit'][i]})
                complete_data_block.append({'facilityId':df['facilityId'][i],'startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'quantity':'VOLUME','kind':'Fjärrvärme','value':df['monthly-volume-consumption'][i],'unit':'m3'})
        
        os.remove(os.path.join(download_dir,f))
        return complete_data_block

def Eforsyning(agentRunContext):
    
    log = Log(agentRunContext)

    if agentRunContext.requestBody.get('targetURL') is None:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,'targetURL is a mandatory parameter')
        return

    try:

        log.job(config.JOB_RUNNING_STATUS,'{0} thread started execution'.format(agentRunContext.requestBody['agentId']))

        thread_id = str(threading.get_ident())
        download_dir = os.path.join(os.getcwd(),'temp','temp-'+thread_id)

        log.info('{0} with threadID {1} has its temp directory in {2}'.format(agentRunContext.requestBody['agentId'],thread_id,download_dir))

        driver = get_driver(download_dir)
        driver.maximize_window()
        driver.get(agentRunContext.requestBody['targetURL'])

        wait = WebDriverWait(driver, 60)
        #document.getElementById('forbrugerNr').value = 'Dhanvi';document.getElementById('kode').value = '1';document.getElementById('login').click();
        wait.until(presence_of_element_located((By.XPATH,'/html/body/div[2]/div[2]/div/mat-dialog-container/dff-cookie-consent-dialog/div/div/mat-dialog-actions/div/button[1]')))

        time.sleep(1.5)

        driver.find_element_by_xpath('/html/body/div[2]/div[2]/div/mat-dialog-container/dff-cookie-consent-dialog/div/div/mat-dialog-actions/div/button[1]').click()

        wait.until(presence_of_element_located((By.ID,'forbrugerNr')))

        time.sleep(1.5)

        print("document.getElementById('forbrugerNr').value = '{0}';document.getElementById('kode').value = '{1}';document.getElementById('login').click();".format(agentRunContext.requestBody['username'],agentRunContext.requestBody['password']))

        # driver.find_element_by_id('mat-tab-label-1-0').click()

        # time.sleep(1)

        driver.find_element_by_id('forbrugerNr').send_keys(agentRunContext.requestBody['username'])

        time.sleep(1)

        driver.find_element_by_id('kode').send_keys(agentRunContext.requestBody['password'])

        time.sleep(1)

        driver.find_element_by_id('login').click();

        time.sleep(1)

        # driver.execute_script("document.getElementById('forbrugerNr').value = '{0}';document.getElementById('kode').value = '{1}';document.getElementById('login').click();".format(agentRunContext.requestBody['username'],agentRunContext.requestBody['password']))

        try:
            wait.until(EC.invisibility_of_element((By.CLASS_NAME,"mat-progress-spinner")))
            wait.until(presence_of_element_located((By.CLASS_NAME,'aktuel-installation')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to login, invalid username or password')
            driver.close()
            os.rmdir(download_dir)
            return
        
        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')
        
        log.info('TargetURL {0}'.format(agentRunContext.requestBody['targetURL']))
        
        try:
            aktuel_installation = driver.find_element_by_class_name('aktuel-installation')
            aktuel_installation_a_tag = aktuel_installation.find_element_by_tag_name('a')
            if len(aktuel_installation_a_tag.get_attribute('href').strip()) == 0:
                raise NoSuchElementException
            time.sleep(2)
            print('There are many facilities')
            try:
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID,'button-spoerg-mig-senere')))
                driver.find_element_by_id('button-spoerg-mig-senere').click()
                time.sleep(2)
            except TimeoutException:
                print('No advertisements')
            aktuel_installation.click()
            time.sleep(2)
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'mat-table')))
            wait.until(EC.invisibility_of_element((By.CLASS_NAME,"mat-progress-spinner")))
            index = 0
            table = driver.find_element_by_class_name('mat-table')
            outer_trs = table.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')
            log.job(config.JOB_RUNNING_STATUS,'Started scraping data')
            downloaded_facilities = 0
            for i in range(len(outer_trs)):
                table = driver.find_element_by_class_name('mat-table')
                tr = table.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')[i]
                tr.click()
                time.sleep(2)
                wait.until(EC.invisibility_of_element((By.CLASS_NAME,"mat-progress-spinner")))
                wait.until(EC.element_to_be_clickable((By.CLASS_NAME,"menu-item-internal")))
        
                driver.find_element_by_class_name("menu-item-internal").click()

                wait.until(EC.element_to_be_clickable((By.CLASS_NAME,"mat-icon-button")))

                driver.find_element_by_class_name('mat-icon-button').click()

                has_downloaded = False
                download_sleep_count = 0
                while(not has_downloaded and download_sleep_count < 25):
                    # print('Now waiting in download')
                    if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-3:] == 'csv' and download_sleep_count < 25 :
                        has_downloaded = True
                    time.sleep(1)
                    download_sleep_count += 1
                if download_sleep_count < 25:
                    complete_data_block = prepare_data(download_dir)
                    log.data(complete_data_block)
                    log.info('Indexed data')
                    downloaded_facilities += 1
                else:
                    print('Download failed')
                    log.info('Download failed for {0}')
                    continue
                driver.back()
                wait.until(EC.invisibility_of_element((By.CLASS_NAME,"mat-progress-spinner")))
            if downloaded_facilities > 0:
                log.job(config.JOB_COMPLETED_SUCCESS_STATUS,'Successfully scraped data for all available facilities')
            else:
                log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to download data for the available facility')
        except NoSuchElementException:
            print('There is only one facility')

            log.job(config.JOB_RUNNING_STATUS,'Started scraping data')
        
            wait.until(EC.element_to_be_clickable((By.CLASS_NAME,"menu-item-internal")))
            
            driver.find_element_by_class_name("menu-item-internal").click()

            wait.until(EC.element_to_be_clickable((By.CLASS_NAME,"mat-icon-button")))

            driver.find_element_by_class_name('mat-icon-button').click()

            has_downloaded = False
            download_sleep_count = 0
            while(not has_downloaded and download_sleep_count < 25):
                # print('Now waiting in download' and download_sleep_count < 25)
                if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-3:] == 'csv' and download_sleep_count < 25 :
                    has_downloaded = True
                else:
                    time.sleep(1)
                    download_sleep_count += 1
            if download_sleep_count < 25:
                complete_data_block = prepare_data(download_dir)
                log.data(complete_data_block)
                log.info('Indexed data')
                log.job(config.JOB_COMPLETED_SUCCESS_STATUS,'Successfully scraped data for all available facilities')
            else:
                print('Download failed')
                log.info('Download failed')
                log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to download data for the available facility')

        

    
    except Exception as e:
        print(traceback.format_exc())
        log.exception(traceback.format_exc())
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))

    driver.close()
    os.rmdir(download_dir)