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

def prepare_data(download_dir,facilityId,unit,quantity):
    for f in os.listdir(download_dir):
        complete_data_block = []
        df = pd.read_csv(os.path.join(download_dir,f),skiprows=[0,13,14],names=['start_date','end_date','consumption','counter_stand','measuring_time'],sep=';')
        for i in range(len(df)):
            if pd.notna(df['consumption'][i]) and pd.notna(df['start_date'][i]) and pd.notna(df['end_date'][i]):
                complete_data_block.append({'facilityId':facilityId,'kind':'Fjärrvärme','quantity':quantity,'unit':unit,'startDate':df['start_date'][i],'endDate':df['end_date'][i],'value':df['consumption'][i]})
        os.remove(os.path.join(download_dir,f))
        del i
        return complete_data_block

def Hofor(agentRunContext):

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
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'emt-login-form-inputs')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,"Not able to load the website")
            driver.close()
            os.rmdir(download_dir)
            return
        
        driver.find_element_by_class_name('emt-cookie-info-button').click()

        time.sleep(2)

        driver.find_element_by_class_name('emt-login-form-inputs').find_elements_by_tag_name('input')[0].send_keys(agentRunContext.requestBody['username'])

        time.sleep(1)

        driver.find_element_by_class_name('emt-login-form-inputs').find_elements_by_tag_name('input')[1].send_keys(agentRunContext.requestBody['password'])

        time.sleep(1)

        driver.execute_script("for(var i=0;i<document.getElementsByTagName('button').length;i++){if(document.getElementsByTagName('button')[i].innerText == 'LOGIN'){document.getElementsByTagName('button')[i].click()}}")
        
        # driver.execute_script("document.getElementsByClassName('emt-login-form-inputs')[0].getElementsByTagName('input')[0].value='{0}';document.getElementsByClassName('emt-login-form-inputs')[0].getElementsByTagName('input')[1].value='{1}';for(var i=0;i<document.getElementsByTagName('button').length;i++){if(document.getElementsByTagName('button')[i].innerText == 'LOGIN'){document.getElementsByTagName('button')[i].click()}};".format(agentRunContext.requestBody['username'],agentRunContext.requestBody['password']))

        wait.until(EC.invisibility_of_element((By.CLASS_NAME,'blockUI')))

        try:
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CLASS_NAME,'emt-menu-section')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,"Unable to login, invalid username or password")
            driver.close()
            os.rmdir(download_dir)
            return
        
        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')
        
        time.sleep(2)

        wait.until(EC.invisibility_of_element((By.CLASS_NAME,'blockUI')))

        driver.execute_script('window.location.href = "http://forbrug.hofor.dk/forbrug/"')

        time.sleep(2)

        wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'emt-consumptionview-itemchooser-container')))

        log.job(config.JOB_RUNNING_STATUS,'Started scraping data')

        itemchooser_div = driver.find_element_by_class_name('emt-consumptionview-itemchooser-container')

        itemchooser_dropdown = itemchooser_div.find_element_by_class_name('emt-dropdown-select-value')

        item_choices = itemchooser_div.find_elements_by_class_name('emt-dropdown-selector-row')

        for choice in item_choices:

            # print(choice.text)
            # facilityId = choice.text.split('-')[2].strip().split()[0]
            

            itemchooser_dropdown.click()

            # time.sleep(2)

            

            # wait.until(EC.invisibility_of_element((By.CLASS_NAME,'blockUI')))

            time.sleep(2)

            select_item = choice.find_element_by_tag_name('a')

            print(select_item.text)
            facilityId = select_item.text.split('-')[2].strip().split()[0]
            print(facilityId)

            select_item.click()

            time.sleep(2)

            # wait.until(EC.invisibility_of_element((By.CLASS_NAME,'blockUI')))

            consumption_view_chooser = driver.find_element_by_class_name('emt-consumptionview-viewchooser-container')

            print(consumption_view_chooser)

            consumption_dropdown = consumption_view_chooser.find_element_by_class_name('emt-dropdown-select-value')

            consumption_item_choices = consumption_view_chooser.find_elements_by_class_name('emt-dropdown-selector-row')

            for i,consumption_choice in enumerate(consumption_item_choices):

                consumption_dropdown.click()

                time.sleep(2)

                consumption_choice_a = consumption_choice.find_element_by_tag_name('a')
                # print(consumption_choice_a.text)

                if i == 0 or i == 1 or i == 4 or i == 6 or i == 5:
                    continue

                if i == 2:
                    unit = 'MWh'
                    quantity = 'ENERGY'
                elif i == 3:
                    unit = 'm3'
                    quantity = 'VOLUME'
                elif i == 5:
                    unit = 'C'
                    quantity = 'TEMPERATURE'

                    # consumption_dropdown.click()

                    # time.sleep(2)

                print(consumption_choice_a.text,i)

                driver.execute_script("document.getElementsByClassName('emt-consumptionview-viewchooser-container')[0].getElementsByClassName('emt-dropdown-selector-content')[0].scrollTo(0,document.getElementsByClassName('emt-consumptionview-viewchooser-container')[0].getElementsByClassName('emt-dropdown-selector-content')[0].scrollHeight);")

                print('scrolled down')

                time.sleep(3)

                consumption_choice_a.click()

                print('clicked on this choice')

                time.sleep(2)

                wait.until(EC.invisibility_of_element((By.CLASS_NAME,'blockUI')))

                date_chooser = driver.find_element_by_class_name('emt-consumptionview-periodchooser-container')

                date_select_value = date_chooser.find_element_by_class_name('emt-date-select-value')

                # date_select_value.click()

                # time.sleep(2)

                month_div = date_chooser.find_elements_by_class_name('emt-date-selector-tab-content')[2]

                choose_year = month_div.find_element_by_class_name('emt-dropdown-select-value')

                # choose_year.click()

                year_choices = month_div.find_elements_by_class_name('emt-dropdown-selector-row')

                search_button = month_div.find_element_by_class_name('emt-date-selector-tab-content-button')

                for year_choice in year_choices:
                    date_select_value.click()

                    time.sleep(2)
                    choose_year.click()
                    time.sleep(2)
                    year_choice_a = year_choice.find_element_by_tag_name('a')
                    
                    print(year_choice_a.text)

                    if year_choice_a.text < '2019':
                        break

                    year_choice_a.click()

                    time.sleep(2)

                    search_button.click()

                    time.sleep(2)

                    wait.until(EC.invisibility_of_element((By.CLASS_NAME,'blockUI')))

                    driver.find_element_by_class_name('emt-comsumption-export-link-hofor').click()

                    has_downloaded = False
                    download_sleep_count = 0
                    while(not has_downloaded and download_sleep_count < 25):
                        # print('Now waiting in download')
                        if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-3:] == 'csv' and download_sleep_count < 25 :
                            has_downloaded = True
                        time.sleep(1)
                        download_sleep_count += 1
                    if download_sleep_count >= 25:
                        print('Download failed')
                        log.info('Download failed for {0}'.format(details))
                        continue

                    complete_data_block = prepare_data(download_dir,facilityId,unit,quantity)

                    log.data(complete_data_block)

                    log.info('Indexed data with facilityId {0}, {1}, {2}'.format(facilityId,quantity,year_choice_a.text))
                    print('Indexed data with facilityId {0}, {1}, {2}'.format(facilityId,quantity,year_choice_a.text))

        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,'Successfully scraped data for all available facilities')

    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())
    
    driver.close()
    os.rmdir(download_dir)