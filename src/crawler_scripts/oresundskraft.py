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
import re

from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from calendar import monthrange


from common import get_driver
from common import Log
import config

def prepare_data(download_dir):
    complete_data_block =[]
    months = {'jan':'jan','feb':'feb','mar':'mar','apr':'apr','maj':'may','jun':'jun','jul':'jul','aug':'aug','sep':'sep','okt':'oct','nov':'nov','dec':'dec'}
    with open(os.path.join(download_dir,os.listdir(download_dir)[0]),encoding='cp1252') as f:
        file_lines = f.readlines()
        kind = file_lines[0].strip()
        facilityId = file_lines[3].split('=')[1].replace('"','').strip()
        index = 6
        for i in range(6,len(file_lines)):
            try:
                file_lines[index]
            except IndexError:
                # print('Done')
                break
            if '=' not in file_lines[index]:
                break
            else:
                extracted_list = [u.replace('"','').replace('=','') for u in file_lines[index].strip().split(';')]
                day = extracted_list[0]
                for key in months.keys():
                    if key in day:
                        day = day.replace(key, months[key])
                # print(extracted_list,index)
                unit = re.sub(r'[^\w\s]','',extracted_list[1].split()[1])
                index += 1
                count = 1
                while('=' in file_lines[index]):
                    extracted_list = [u.replace('"','').replace('=','') for u in file_lines[index].strip().split(';')]
                    startdate = parse(day+' '+"{:02d}".format(int(extracted_list[0].split('-')[0])%24))
                    enddate = parse(day+' '+"{:02d}".format(int(extracted_list[0].split('-')[1])%24))
                    value = extracted_list[1]
                    complete_data_block.append({'facilityId':facilityId,'kind':kind,'quantity':'ENERGY','unit':unit,'startDate':dt.strftime(startdate,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(enddate,'%Y-%m-%d %H:%M:%S'),'value':value})
                    count += 1
                    index += 1
                index += 2
    os.remove(os.path.join(download_dir,os.listdir(download_dir)[0]))
    return complete_data_block,facilityId

def Oresundskraft(agentRunContext):

    log = Log(agentRunContext)

    try:

        log.job(config.JOB_RUNNING_STATUS,'{0} thread started execution'.format(agentRunContext.requestBody['agentId']))

        thread_id = str(threading.get_ident())
        download_dir = os.path.join(os.getcwd(),'temp','temp-'+thread_id)

        log.info('{0} with threadID {1} has its temp directory in {2}'.format(agentRunContext.requestBody['agentId'],thread_id,download_dir))

        driver = get_driver(download_dir)
        driver.maximize_window()
        driver.get(agentRunContext.homeURL)

        wait = WebDriverWait(driver,120)

        try:
            wait.until(EC.element_to_be_clickable((By.ID,'login')))
        except TimeoutException:
            print(traceback.format_exc())
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Not able to load the website')
            log.info('Timeout exception occured while waiting for login div')
            driver.close()
            os.rmdir(download_dir)
            return

        #Login script

        driver.find_element_by_class_name('cc-dismiss').click()

        time.sleep(1)

        login_div = driver.find_element_by_id('login')

        login_div.find_elements_by_class_name('form-control')[0].send_keys(agentRunContext.requestBody['username'])
        login_div.find_elements_by_class_name('form-control')[1].send_keys(agentRunContext.requestBody['password'])

        login_div.find_element_by_class_name('btnn').click()

        try:
            wait.until(EC.visibility_of_element_located((By.ID,'energy-portal-container')))
        except TimeoutException:
            print(traceback.format_exc())
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to login, invalid username or password')
            log.info('Timeout exception occured while waiting for portal-container div')
            driver.close()
            os.rmdir(download_dir)
            return
        
        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')

        bread_crumbs = driver.find_element_by_class_name('breadcrumbs')

        facility = bread_crumbs.find_elements_by_class_name('muted')[1]

        facility.click()

        wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'navmodal')))

        while("display: none" in driver.find_element_by_class_name('navmodal').get_attribute('style')):
            time.sleep(1)
        navmodal_div = driver.find_element_by_class_name('navmodal')
        modalpanel_kundnummer = navmodal_div.find_elements_by_class_name('modalpanel')[0]
        modalpanel_address = navmodal_div.find_elements_by_class_name('modalpanel')[1]

        kundnummer_a_tags = modalpanel_kundnummer.find_elements_by_tag_name('a')

        address_a_tags = modalpanel_address.find_elements_by_tag_name('a')

        log.job(config.JOB_RUNNING_STATUS,'Started scraping data')

        for i in range(len(kundnummer_a_tags)):
            bread_crumbs = driver.find_element_by_class_name('breadcrumbs')

            facility = bread_crumbs.find_elements_by_class_name('muted')[1]

            facility.click()

            wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'navmodal')))

            wait.until(EC.invisibility_of_element((By.CLASS_NAME,'loading-spinner')))

            while("display: none" in driver.find_element_by_class_name('navmodal').get_attribute('style')):
                time.sleep(1)
            navmodal_div = driver.find_element_by_class_name('navmodal')
            modalpanel_kundnummer = navmodal_div.find_elements_by_class_name('modalpanel')[0]

            kundnummer_a_tags = modalpanel_kundnummer.find_elements_by_tag_name('a')

            kundnummer_a_tags[i].click()

            time.sleep(2)

            address_a_tags = modalpanel_address.find_elements_by_tag_name('a')

            for j in range(len(address_a_tags)):
                bread_crumbs = driver.find_element_by_class_name('breadcrumbs')

                facility = bread_crumbs.find_elements_by_class_name('muted')[1]

                facility.click()

                wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'navmodal')))

                wait.until(EC.invisibility_of_element((By.CLASS_NAME,'loading-spinner')))

                while("display: none" in driver.find_element_by_class_name('navmodal').get_attribute('style')):
                    time.sleep(1)
                
                navmodal_div = driver.find_element_by_class_name('navmodal')
                modalpanel_address = navmodal_div.find_elements_by_class_name('modalpanel')[1]
                address_a_tags = modalpanel_address.find_elements_by_tag_name('a')
                address_a_tags[j].click()

                time.sleep(2)

                wait.until(EC.invisibility_of_element((By.CLASS_NAME,'loading-spinner')))

                left_frame = driver.find_element_by_class_name('frame-left')

                submenu_facilities = left_frame.find_element_by_class_name('submenu')

                facility_data = submenu_facilities.find_elements_by_tag_name('a')

                for a_tag in facility_data:
                    if 'display: none' in a_tag.get_attribute('style'):
                        continue
                    facility_kind = a_tag.text

                    a_tag.click()

                    time.sleep(4)

                    driver.execute_script("buttons=document.getElementsByClassName('period-button');for(var i=0;i<buttons.length;i++){if(buttons[i].innerText == 'Dag'){buttons[i].click()}}")

                    wait.until(EC.invisibility_of_element((By.CLASS_NAME,'loading-spinner')))

                    download_button = driver.find_element_by_css_selector('a.filter-button.mr-2')

                    #get data monthly only

                    href = download_button.get_attribute('href')

                    # print(href)

                    start_date = dt(2020,1,1)
                    while(start_date < dt.now()):
                        end_date = start_date + relativedelta(months=1)
                        link_split = href.split('/')
                        link_split[7] = dt.strftime(start_date, "%Y-%m-%d")
                        link_split[8] = dt.strftime(end_date, "%Y-%m-%d")
                        driver.execute_script("window.location.href = '{0}';".format('/'.join(link_split)))
                        start_date = start_date + relativedelta(months=1)
                        has_downloaded = False
                        download_sleep_count = 0
                        while(not has_downloaded  and download_sleep_count < 25):
                            # print('Now waiting in download')
                            if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-3:] == 'csv' and download_sleep_count < 25 :
                                has_downloaded = True
                            time.sleep(1)
                            download_sleep_count += 1
                        if download_sleep_count >= 25:
                            print('Download failed')
                            log.info('Download failed for {0}'.format(details))
                            continue

                        complete_data_block,facilityId = prepare_data(download_dir)

                        log.data(complete_data_block)

                        log.info('Indexed data with facilityid {0}'.format(facilityId))

                # print('Done here')
        
        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,'Successfully scraped data for all available facilities')

        #breadcrumbs

            #/api/oows/getConsumptionExport/827008/2017-01-01/2017-01-07/day/EL/?address=Bunkalundsv%C3%A4gen%206,%20Helsingborg&installationNumbers=38666001&installationNumbers=38666001

    except Exception as e:
        print(traceback.format_exc())
        log.exception(traceback.format_exc())
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))

    driver.close()
    os.rmdir(download_dir)