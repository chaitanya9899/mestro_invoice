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

import json

def prepare_data(download_dir,facilityId,kind):
    for f in os.listdir(download_dir):
        header = ['meterno','date','meterreading','unit','consumption','annual','status']
        df = pd.read_csv(os.path.join(download_dir,f),skiprows=[0],names=header)
        prev_end_date = None
        prev_unit = None
        consumption = 0
        complete_data_block = []
        for i in range(len(df)):
            if df['status'][i] != 'Normal' or df['unit'][i] == 'kVAr' or df['unit'][i] == 'kVA':
                continue
            end_date = parse(df['date'][i])
            if prev_end_date == None:
                prev_end_date = end_date
            if prev_unit == None:
                prev_unit = df['unit'][i]
            if prev_end_date == end_date and prev_unit == df['unit'][i]:
                consumption += float(df['consumption'][i].replace(',','.'))
            else:
                start_date = prev_end_date - relativedelta(months=1)
                if prev_unit == 'kWh' or prev_unit == 'MWh':
                    quantity = 'ENERGY'
                elif prev_unit == 'kW':
                    quantity = 'POWER'
                elif prev_unit == 'm3':
                    quantity = 'VOLUME'
                complete_data_block.append({'endDate':dt.strftime(prev_end_date,'%Y-%m-%d %H:%M:%S'),'startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'value':str(consumption).replace('.',','),'unit':prev_unit,'facilityId':facilityId,'quantity':quantity,'kind':kind})
                consumption = float(df['consumption'][i].replace(',','.'))
            prev_end_date = end_date
            prev_unit = df['unit'][i]
        os.remove(os.path.join(download_dir,f))
        return complete_data_block

def KalmarEnergi(agentRunContext):
    log = Log(agentRunContext)

    try:
        log.job(config.JOB_RUNNING_STATUS,'{0} thread started execution'.format(agentRunContext.requestBody['agentId']))

        thread_id = str(threading.get_ident())
        download_dir = os.path.join(os.getcwd(),'temp','temp-'+thread_id)

        log.info('{0} with threadID {1} has its temp directory in {2}'.format(agentRunContext.requestBody['agentId'],thread_id,download_dir))

        driver = get_driver(download_dir)
        driver.maximize_window()
        driver.get(agentRunContext.homeURL)

        base_path = os.path.split(agentRunContext.homeURL)[0]

        wait = WebDriverWait(driver,100)

        try:
            wait.until(presence_of_element_located((By.ID,'tabCustomernumber')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Not able to load the website')
            driver.close()
            os.rmdir(download_dir)
            return()

        driver.execute_script("document.getElementById('tabCustomernumber').click();document.getElementById('txtUser').value = '{0}';document.getElementById('txtPassword').value = '{1}';document.getElementById('btnLogin').click();".format(agentRunContext.requestBody['username'],agentRunContext.requestBody['password']))

        time.sleep(1)

        try:
            wait.until(presence_of_element_located((By.XPATH,'/html/body/form/nav/div[2]/ul/li[1]/a')))
        except TimeoutException as e:
            try:
                driver.find_element_by_id('AlertLockedAccount')
                log.job(config.JOB_COMPLETED_FAILED_STATUS,'Account is locked')
            except NoSuchElementException:
                try:
                    driver.find_element_by_id('AlertLoginError')
                    log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to login, invalid username or password')
                except NoSuchElementException:
                    log.job(config.JOB_COMPLETED_FAILED_STATUS, "Unable to load website")
            driver.close()
            return

        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')

        important_ds = {}

        important_ds_addr = {}

        start = time.time()

        driver.execute_script('window.location.href = "{0}/Contract/Contracts.aspx";'.format(base_path))

        log.info('window.location.href = "{0}/Contract/Contracts.aspx";'.format(base_path))

        time.sleep(1)

        #Wait until the loader is invisible
        wait.until(EC.invisibility_of_element_located((By.XPATH,'/html/body/form/div[3]/div[4]')))

        try:
            div_addrs = driver.find_element_by_id('UsePlaceContainer')
        except NoSuchElementException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Not able to load facilities details')
            driver.close()
            os.rmdir(download_dir)
            return

        options = div_addrs.find_elements_by_tag_name('option')

        for option in options:
            use_place_ids = option.get_attribute('value').split(',')

            for upid in use_place_ids:
                important_ds_addr[upid] = option.text
        
        log.info(str(important_ds_addr))

        # log.info('time taken for only addr is {0}'.format(time.time() - start))

        contractDetails = driver.find_element_by_id("ContractDetails")
        
        divs = contractDetails.find_elements_by_class_name("filtered-status")

        log.job(config.JOB_RUNNING_STATUS,'Started gathering facility ids')

        for div in divs:
            service_identifier = div.get_attribute('data-serviceidentifier')
            utility_id = div.get_attribute('data-utilityid')
            useplace_id = div.get_attribute('data-useplaceid')
            if ((service_identifier.strip() == '-' or len(service_identifier.strip()) == 1) and len(div.find_elements_by_class_name("space-10")) > 0):
                service_identifier = important_ds_addr[useplace_id]
            if important_ds.get(useplace_id) is not None:
                important_ds[useplace_id][utility_id] = service_identifier
            else:
                important_ds[useplace_id] = {utility_id:service_identifier}
        
        index = 2
        selected_index = 2

        driver.find_element_by_xpath('/html/body/form/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/button/div/div').click()

        while(1):
            # print(index)

            try:
                li = driver.find_element_by_xpath('/html/body/form/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[2]/ul/li[{0}]'.format(index))
                click_a = li.find_element_by_tag_name('a')
            except NoSuchElementException as e:
                break
            
            if 'selected' in li.get_attribute("class") and index == selected_index:
                click_a.click()
                index += 1
                continue
            else:
                click_a.click()
                selected_index = index

            driver.find_element_by_xpath('/html/body/form/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/button/div/div').click()

            wait.until(EC.invisibility_of_element_located((By.XPATH,'/html/body/form/div[3]/div[4]')))

            contractDetails = driver.find_element_by_id("ContractDetails")

            divs = contractDetails.find_elements_by_class_name("filtered-status")

            for div in divs:
                service_identifier = div.get_attribute('data-serviceidentifier')
                utility_id = div.get_attribute('data-utilityid')
                useplace_id = div.get_attribute('data-useplaceid')
                if ((service_identifier.strip() == '-' or len(service_identifier.strip()) == 1) and len(div.find_elements_by_class_name("space-10")) > 0):
                    service_identifier = important_ds_addr[useplace_id]
                if important_ds.get(useplace_id) is not None:
                    important_ds[useplace_id][utility_id] = service_identifier
                else:
                    important_ds[useplace_id] = {utility_id:service_identifier}
            
            index += 1

            driver.execute_script('window.scrollTo(0,0);')
            
            time.sleep(1)

            driver.find_element_by_xpath('/html/body/form/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/button/div/div').click()

            click_a.click()
        
        # log.info(str(important_ds))
        print(important_ds)

        #/Consumption/HistoricalMeterReadings.aspx

        driver.execute_script('window.location.href = "{0}/Consumption/HistoricalMeterReadings.aspx";'.format(base_path))

        log.info('window.location.href = "{0}/Consumption/HistoricalMeterReadings.aspx";'.format(base_path))

        useplace_id_chronological = []

        wait.until(EC.element_to_be_clickable((By.ID,"UsePlaceContainer")))

        # useplace_container = driver.find_element_by_id('UsePlaceContainer')

        # useplace_container_options = useplace_container.find_elements_by_tag_name('option')

        useplace_container_select = driver.find_element_by_id('UsePlaceDropDownMenu')

        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,"ajax-loading")))
        time.sleep(3)
        
        useplace_container_optgroup = useplace_container_select.find_element_by_tag_name('optgroup')

        useplace_container_options = useplace_container_optgroup.find_elements_by_tag_name('option')

        for i,up_option in enumerate(useplace_container_options):
            useplace_id_chronological.append(up_option.get_attribute('value'))
        
        print(useplace_id_chronological)

        available_resolution = {'E':'Timme','V':'Dag','F':'Dag','G':'Timme','K':'Dag','P':'Dag'}

        accessKey = {'El':'E','Vatten':'V','Fjärrvärme':'F','Fjärrkyla':'K','Naturgas':'G','El Produktion':'P'}

        for i in range(len(useplace_id_chronological)):
            useplace_container = driver.find_element_by_id('UsePlaceContainer')
            useplace_button = useplace_container.find_element_by_tag_name('button')
            useplace_button.click()
            time.sleep(2)
            dropdown_menu = useplace_container.find_element_by_class_name('dropdown-menu')
            dropdown_menu_ul = dropdown_menu.find_element_by_tag_name('ul')
            curr_li = dropdown_menu_ul.find_elements_by_tag_name('li')[i+1]
            address_click_a = curr_li.find_element_by_tag_name('a')
            address_click_a.click()
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,"ajax-loading")))
            time.sleep(3)
            utility_type_container = driver.find_element_by_id('UtilityTypeContainer')
            utility_type_container_button = utility_type_container.find_element_by_tag_name('button')
            utility_type = utility_type_container_button.find_element_by_class_name('filter-option-inner-inner').text.strip().split()[0]
            access_key = accessKey[utility_type]
            if important_ds.get(useplace_id_chronological[i]) is not None:
                export = driver.find_element_by_id('export')
                export_items = export.find_elements_by_tag_name('li')
                facilityId = important_ds.get(useplace_id_chronological[i])[access_key]
                print(facilityId)
                outer_button = driver.find_element_by_xpath('/html/body/form/div[3]/div/div[2]/div[2]/div[4]/div[1]/div/div/div/span')
                outer_button.click()
                for export_item in export_items:
                    a_tag = export_item.find_element_by_tag_name('a')
                    if a_tag.text == 'csv':
                        a_tag.click()
                        has_downloaded = False
                        download_sleep_count = 0
                        while(not has_downloaded and download_sleep_count < 15):
                            if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-3:] == 'csv' and download_sleep_count < 15 :
                                has_downloaded = True
                            time.sleep(1)
                            download_sleep_count += 1
                        if download_sleep_count < 15:
                            complete_data_block = prepare_data(download_dir,facilityId,utility_type)
                            log.data(complete_data_block)
                            log.info('Indexed data for facilityId {0}'.format(facilityId))
                        else:
                            print('Download failed')
                            log.info('Download failed for {0}'.format(facilityId))

        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,"Successfully scraped data for all available facilities")
    
    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())
    
    driver.close()
    os.rmdir(download_dir)