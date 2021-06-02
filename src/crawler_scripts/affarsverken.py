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

def Affarsverken(agentRunContext):

    log = Log(agentRunContext)

    try:

        log.job(config.JOB_RUNNING_STATUS,'{0} thread started execution'.format(agentRunContext.requestBody['agentId']))

        thread_id = str(threading.get_ident())
        download_dir = os.path.join(os.getcwd(),'temp','temp-'+thread_id)

        log.info('{0} with threadID {1} has its temp directory in {2}'.format(agentRunContext.requestBody['agentId'],thread_id,download_dir))

        driver = get_driver(download_dir)
        driver.maximize_window()
        driver.get(agentRunContext.homeURL)

        # base_path = os.path.split(agentRunContext.homeURL)[0]

        wait = WebDriverWait(driver,100)

        wait.until(presence_of_element_located((By.ID,"Login1_UserName")))

        login_script = "document.getElementById('Login1_UserName').value='{0}';document.getElementById('Login1_Password').value='{1}';document.getElementById('Login1_Login').click();".format(agentRunContext.requestBody['username'],agentRunContext.requestBody['password'])

        driver.execute_script(login_script)

        try:
            WebDriverWait(driver,60).until(presence_of_element_located((By.ID,'column-menu')))
        except TimeoutException as e:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to login, invalid username or password')
            driver.close()
            os.rmdir(downloda_dir)
            return
        
        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')

        try:
            log.job(config.JOB_RUNNING_STATUS,'Started scraping el data')

            driver.execute_script("window.location.href = '/Foretag/Mina-sidor/El/Timvarden/';")

            wait.until(presence_of_element_located((By.ID,'ctl00_WideContentRow_ddlUtilities_chosen')))

            index = 1

            header_timme = ['date']

            for i in range(24):
                header_timme.append("{:02d}".format(i)+":00:00")

            header_monthly = ['date','mileage','consumption','annual']

            log.job(config.JOB_RUNNING_STATUS,'Started scraping el data')

            while(1):

                print(index)

                try:
                    driver.find_element_by_id('ctl00_WideContentRow_ddlUtilities_chosen').click()
                    time.sleep(2)
                    driver.find_element_by_xpath('/html/body/div[1]/div[1]/form/div[6]/div/div[2]/div[1]/div[5]/div/div/div/ul/li[{0}]'.format(index)).click()
                    wait.until(EC.invisibility_of_element_located((By.ID,'AjaxLoader')))
                except NoSuchElementException as e:
                    log.job(config.JOB_RUNNING_STATUS,'Successfully scraped el data for all available facilities')
                    break
                
                isHourMeasurement = driver.find_element_by_id('HiddenIsHourMeasuresInstallation').get_attribute('value')

                facilityId = driver.find_element_by_id('ctl00_WideContentRow_hidUtilityID').get_attribute('value')

                if(isHourMeasurement == "True"):

                    from_date = dt.strftime(dt.now() - relativedelta(months=12),"%Y-%m-%d")

                    driver.execute_script("document.getElementById('ctl00_WideContentRow_txtFromDate').value = '{0}';GetValues()".format(from_date))

                    wait.until(EC.invisibility_of_element_located((By.ID,'AjaxLoader')))

                    time.sleep(2)

                    table_div = driver.find_element_by_class_name('values-table-holder')

                    table = table_div.find_element_by_tag_name('table')

                    tbody = table.find_element_by_tag_name('tbody')

                    trs = tbody.find_elements_by_tag_name('tr')

                    final_data = []

                    for tr in trs:
                        val_split = tr.text.split()
                        final_data.append([val_split[i].strip() for i in range(25)])
                    
                    df = pd.DataFrame(final_data,columns=header_timme)

                    complete_data_block = []

                    for i in range(len(df)):
                        for j in range(1,len(header_timme)):
                            start_date = parse(df['date'][i].replace('‑','-')+' '+header_timme[j])
                            end_date = start_date + relativedelta(hours=1)
                            complete_data_block.append({'facilityId':facilityId,'value':df[header_timme[j]][i],'startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'kind':'El','quantity':'ENERGY','unit':'kWh'})

                else:

                    log.info('Here in no time for {0}, so getting monthly data'.format(facilityId))

                    driver.execute_script('window.location.href = "/Foretag/Mina-sidor/El/Avlasningar/"')

                    time.sleep(2)

                    wait.until(EC.invisibility_of_element_located((By.ID,'AjaxLoader')))

                    table_div = driver.find_element_by_id('ReadingsHolder')

                    table = table_div.find_element_by_tag_name('table')

                    tbody = table.find_element_by_tag_name('tbody')

                    trs = tbody.find_elements_by_tag_name('tr')

                    final_list = []

                    for tr in trs:
                        final_list.append(tr.text.split())
                    
                    df = pd.DataFrame(final_list,columns=header_monthly)

                    complete_data_block = []

                    for i in range(len(df)):
                        end_date = parse(df['date'][i].replace('‑','-'))
                        start_date = end_date - relativedelta(days=(end_date.day - 1))
                        complete_data_block.append({'facilityId':facilityId,'kind':'El','quantity':'ENERGY','unit':'kWh','startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['consumption'][i]})
                    
                    driver.execute_script("window.location.href = '/Foretag/Mina-sidor/El/Timvarden/';")

                    time.sleep(2)
                
                log.data(complete_data_block)
                log.info('Indexed data for facility_id {0}'.format(facilityId))
                index += 1

        except TimeoutException:
            log.info('No electricity data for this user')
            log.job(config.JOB_RUNNING_STATUS,'No electricity data for this user')
        
        try:
            log.job(config.JOB_RUNNING_STATUS,'Started scraping varme data')

            driver.execute_script('window.location.href = "/Foretag/Mina-sidor/Varme/Avlasningar"')

            wait.until(presence_of_element_located((By.ID,'ctl00_WideContentRow_WideContent_ddlUtilities_chosen')))

            index = 1

            header_heating = ['date','consumption-mil','consumption-mwh','dmp1','dmp2','flow-mil','flow-consumption']

            while(1):

                print(index)

                try:
                    driver.find_element_by_id('ctl00_WideContentRow_WideContent_ddlUtilities_chosen').click()
                    time.sleep(2)
                    driver.find_element_by_xpath('/html/body/div[1]/div[1]/form/div[6]/div/div/div[1]/div[5]/div/div/div/ul/li[{0}]'.format(index)).click()
                    wait.until(EC.invisibility_of_element_located((By.ID,'AjaxLoader')))
                except NoSuchElementException as e:
                    log.job(config.JOB_RUNNING_STATUS,'Successfully scraped varme data for all available facilities')
                    break
                
                facilityId = driver.find_element_by_id('ctl00_WideContentRow_WideContent_hidUtilityID').get_attribute('value')

                table_div = driver.find_element_by_id('ReadingsHolder')

                table = table_div.find_element_by_tag_name('table')

                tbody = table.find_element_by_tag_name('tbody')

                trs = tbody.find_elements_by_class_name('zebra')

                flode_list = []

                for tr in trs:
                    flode_list.append(tr.text.split())
                    tr.find_element_by_tag_name('td').click()
                    time.sleep(0.5)
                
                df = pd.DataFrame(flode_list,columns=header_heating)

                complete_data_block = []

                for i in range(len(df)):
                    end_date = parse(df['date'][i])
                    start_date = end_date - relativedelta(days=(end_date.day - 1))
                    if df['flow-consumption'][i] is not None:
                        complete_data_block.append({'facilityId':facilityId,'kind':'Fjärrvärme','quantity':'VOLUME','unit':'m3','startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['flow-consumption'][i]})
                
                log.data(complete_data_block)

                complete_data_block = []

                trs_dag = tbody.find_elements_by_class_name('sub-table')

                data_list = []

                header_heating2 = ['date','consumption-mwh','dmp2','flow-consumption']

                for tr in trs_dag:
                    data_list.append(tr.text.split())
                
                df = pd.DataFrame(data_list,columns=header_heating2)

                for i in range(len(df)):
                    start_date = parse(df['date'][i])
                    end_date = start_date + relativedelta(days=1)
                    complete_data_block.append({'facilityId':facilityId,'kind':'Fjärrvärme','quantity':'ENERGY','unit':'MWh','startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['consumption-mwh'][i]})
                
                log.data(complete_data_block)

                log.info('Indexed data for facility_id {0}'.format(facilityId))

                index += 1
        
        except TimeoutException:
            log.info('No varme data for this user')
            log.job(config.JOB_RUNNING_STATUS,'No varme data for this user')

        
        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,'Successfully scraped data for all available facilities')

    except Exception as e:
        print(traceback.format_exc())
        log.exception(traceback.format_exc())
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))

    driver.close()
    os.rmdir(download_dir)