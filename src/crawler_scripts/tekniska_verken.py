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
import json

from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from calendar import monthrange


from common import get_driver
from common import Log
import config

def prepare_data(download_dir,facilitytype,resolution):
    with open(os.path.join(download_dir,os.listdir(download_dir)[0]), 'r', encoding='utf-8-sig') as f:
        tekniska_obj = json.loads(f.read())
    complete_data_block = []
    try:
        consumption = tekniska_obj['Användning']
    except TypeError:
        os.remove(os.path.join(download_dir,os.listdir(download_dir)[0]))
        return None,None
    data_block = {}
    facilityId = tekniska_obj['Anl id']
    for c in consumption:
        if resolution == 'month':
            year = int(c['År'])
            month = int(c['Månad'])
            start_date = parse( c['År'] + '-' + c['Månad'] + '-01')
            end_date = parse(c['År'] + '-' + c['Månad'] + '-' + str(monthrange(year,month)[1]))
        if resolution == 'day':
            start_date = parse(c['År'] + '-' + c['Månad'] + '-' + c['Dag'])
            end_date = start_date + relativedelta(days=1)
        if resolution == 'hour':
            start_date = parse(c['År'] + '-' + c['Månad'] + '-' + c['Dag'] + ' ' + "{:02d}".format(int(c['Timme'])%24))
            end_date = start_date + relativedelta(hours=1)
        if facilitytype == 'El' or facilitytype == 'Fjärrvärme':
            quantity = 'ENERGY'
            unit = 'kWh'
        if facilitytype == 'Avfall':
            quantity = 'WEIGHT'
            unit = 'kg'
        if facilitytype == 'Vatten':
            quantity = 'VOLUME'
            unit = 'm3'
        complete_data_block.append({'facilityId':facilityId,'kind':facilitytype,'quantity':quantity,'unit':unit,'startDate':dt.strftime(start_date, "%Y-%m-%d %H:%M:%S"),'endDate':dt.strftime(end_date, "%Y-%m-%d %H:%M:%S"),'value':c['Värde']})
        # data_block = {'facilityid': , 'kind': facilitytype}
        # data_block['quantity'] = Quantity
        # data_block['unit'] = Unit
        # data_block['startDate'] = dt.strftime(start_date, "%Y-%m-%d %H:%M:%S")
        # data_block['endDate'] = dt.strftime(end_date, "%Y-%m-%d %H:%M:%S")
        # data_block['value'] = c['Värde']
        # complete_data_block.append(data_block)
    os.remove(os.path.join(download_dir,os.listdir(download_dir)[0]))
    return complete_data_block,facilityId

def TekniskaVerken(agentRunContext):
    
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

        #document.getElementById('orgainsationlogin').click();document.getElementById('UserName').value = '1112600';document.getElementById('Password').value = '7960';document.getElementById('loginbutton').click();

        try:
            wait.until(EC.element_to_be_clickable((By.ID,'cookieOK')))
            driver.find_element_by_id('cookieOK').click()
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to load the website')
            driver.close()
            os.rmdir(download_dir)
            return
        except NoSuchElementException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Not able to accept cookies')
            driver.close()
            os.rmdir(download_dir)
            return

        wait.until(EC.element_to_be_clickable((By.ID,'orgainsationlogin')))

        driver.find_element_by_id('orgainsationlogin').click()

        wait.until(EC.visibility_of_element_located((By.ID,'UserName')))

        driver.execute_script("document.getElementById('UserName').value = '{0}';document.getElementById('Password').value = '{1}';document.getElementById('loginbutton').click();".format(agentRunContext.requestBody['username'],agentRunContext.requestBody['password']))
        
        try:
            wait.until(presence_of_element_located((By.ID,'mpselectaccount-list')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to login, wrong username or password')
            driver.close()
            os.rmdir(download_dir)
            return
        
        log.job(config.JOB_RUNNING_STATUS, "Logged in successfully")
        
        users_table = driver.find_element_by_id('mpselectaccount-list')

        user_rows = users_table.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')

        user_page_list = []

        for row in user_rows:
            user_page_list.append(row.find_element_by_tag_name('a').get_attribute('href'))
        
        log.job(config.JOB_RUNNING_STATUS, "Started scraping data")
        
        for user_acc in user_page_list:
            driver.execute_script("window.location.href = '{0}';".format(user_acc))

            time.sleep(2)

            driver.execute_script("window.scrollTo(0,1250);")

            time.sleep(2)

            # while('display: block' not in driver.find_element_by_class_name('mypages-usage-list-wrapper').get_attribute('style')):
            #     time.sleep(1)

            wait.until(EC.visibility_of_element_located((By.CLASS_NAME,"mypages-usage-services")))
            time.sleep(1)
            
            usage_service_div = driver.find_element_by_class_name("mypages-usage-services")

            #mypages-usage-services-service

            services = usage_service_div.find_elements_by_class_name("mypages-usage-services-service")
            print(len(services))
            if len(services) == 0:
                services = usage_service_div.find_elements_by_class_name("mypages-usage-services-service-no-data")

            service_links = []

            for service in services:

                service_links.append(service.find_element_by_tag_name('a').get_attribute('href'))
            
            for service_link in service_links:

                if 'farligt-avfall' in service_link or 'container' in service_link:
                    continue

                driver.execute_script("window.location.href = '{0}'".format(service_link))

                time.sleep(2)

                wait.until(EC.element_to_be_clickable((By.CLASS_NAME,"mypages-dropdown-button")))

                ul = driver.find_element_by_class_name("mypages-dropdown-list")

                lis = ul.find_elements_by_tag_name("li")

                delivery_points = []

                for li in lis:
                    delivery_points.append(li.find_element_by_tag_name('a').get_attribute('href'))
                
                for delivery_point in delivery_points:
                    driver.execute_script("window.location.href = '{0}'".format(delivery_point))

                    time.sleep(2)

                    try:
                        wait.until(EC.element_to_be_clickable((By.CLASS_NAME,"mypages-utility-graph-chart-header-button")))
                    except TimeoutException:
                        log.info('No data available for deliverypoint {0}'.format(delivery_point))
                        continue

                    facilitytype = driver.find_element_by_class_name('mypages-heading').text

                    time.sleep(1)

                    driver.find_element_by_class_name("mypages-utility-graph-chart-header-button").click()

                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME,"mypages-utility-graph-chart-header-export-icon")))

                
                    driver.find_element_by_class_name("mypages-utility-graph-chart-header-export-icon").click()

                    wait.until(EC.element_to_be_clickable((By.ID,'from')))

                    start_date = dt.now() - relativedelta(years=1)

                    driver.execute_script("document.getElementById('from').value = '{0}'".format(dt.strftime(start_date,"%Y-%m-%d")))

                    time.sleep(2)

                    # driver.find_element_by_id('from').clear()
                    # start_date = dt.now() - relativedelta(years=1)
                    # driver.find_element_by_id('from').send_keys()

                    # time.sleep(2)

                    # wait.until(EC.element_to_be_clickable((By.ID,'mesyear')))

                    resolution_array = driver.find_element_by_class_name("form-resolution-items")

                    available_resolutions = resolution_array.find_elements_by_tag_name('input')

                    total_len = len(available_resolutions)

                    resolution = available_resolutions[len(available_resolutions)-1].get_attribute('data-resolution')

                    resolution_id = available_resolutions[len(available_resolutions)-1].get_attribute('id')

                    print(available_resolutions[len(available_resolutions)-1].get_attribute('id'))

                    # driver.find_element_by_class_name("form-resolution-items").find_elements_by_tag_name('input')[total_len-1].click()

                    # driver.find_element_by_id(resolution_id).click()

                    driver.execute_script("document.getElementById('{0}').click();".format(resolution_id))

                    time.sleep(2)

                    # available_resolutions[len(available_resolutions)-1].click()

                    driver.execute_script("for(var i=0;i<document.getElementsByName('exportformat').length;i++){if(document.getElementsByName('exportformat')[i].getAttribute('value') == 'json'){document.getElementsByName('exportformat')[i].click()}}")

                    time.sleep(2)

                    # driver.find_element_by_id('exportbutton').click()

                    driver.execute_script("document.getElementById('exportbutton').click();")

                    time.sleep(2)

                    has_downloaded = False
                    download_sleep_count = 0

                    while(not has_downloaded and download_sleep_count < 30):
                        if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-4:] == 'json' and download_sleep_count < 30 :
                            has_downloaded = True
                        time.sleep(1)
                        download_sleep_count += 1
                    
                    if download_sleep_count >= 30:
                        log.info('Download failed for')
                        continue

                    complete_data_block,facilityId = prepare_data(download_dir,facilitytype,resolution)

                    if complete_data_block == None and facilityId == None:
                        log.info('No data available for deliverypoint {0}'.format(delivery_point))
                        continue

                    log.data(complete_data_block)

                    log.info('Indexed data with facilityId {0}'.format(facilityId))
        
        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,"Successfully scraped data of all available facilities")

    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())
    
    driver.close()
    os.rmdir(download_dir)