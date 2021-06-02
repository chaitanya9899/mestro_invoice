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

def hour_rounder(t):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return (t.replace(second=0, microsecond=0, minute=0, hour=t.hour)+timedelta(hours=t.minute//30))

def prepare_data(download_dir,facilityId,kind,resolution,quantity):
    complete_data_block = []
    for f in os.listdir(download_dir):
        df = pd.read_excel(os.path.join(download_dir,os.listdir(download_dir)[0]),skiprows=[0])
        excel_columns = list(df.columns)
        if quantity == "ENERGY" or quantity == "POWER":
            names = ['date','consumption','temp']
            unit = excel_columns[1].split()[1].replace('(','').replace(')','')
        if quantity == "VOLUME":
            names = ['date','consumption']
            unit = 'm3'
        df.columns = names
        for j in range(len(df)):
            if pd.notna(df['date'][j]) and pd.notna(df['consumption'][j]):
                start_date = hour_rounder(df['date'][j].to_pydatetime())
                if resolution == 'Timme' or resolution == 'Timmedel':
                    end_date = start_date + relativedelta(hours=1)
                if resolution == 'Dag' or resolution == 'Dygnsmedel':
                    end_date = start_date + relativedelta(days=1)
                if resolution == 'Månad':
                    end_date = start_date + relativedelta(months=1)
                if resolution == 'År':
                    end_date = start_date + relativedelta(years=1)
                # if quantity == "Energi":
                #     q = 'ENERGY'
                # if quantity == 'Flöde':
                #     q = 'VOLUME'
                # if quantity == 'Delta-T':
                #     q = 'TEMPERATURE'
                complete_data_block.append({'facilityId':facilityId,'kind':kind,'unit':unit,'quantity':quantity,'startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['consumption'][j]})
        os.remove(os.path.join(download_dir,f))
        # time.sleep(1)
        # print('Hrererrrrerere',os.listdir(download_dir))
        return complete_data_block

#I have to also get a facilityId, address dictionary as parameter
def select_and_download_data(wait,driver,log,download_dir,quantity):
    index = 0
    while(1):
        time.sleep(2)
        wait.until(EC.invisibility_of_element((By.CLASS_NAME,"loading-wrapper")))
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'premise-toggle')))
        premise_toggle = driver.find_element_by_class_name('premise-toggle')
        premise_toggle_button = premise_toggle.find_element_by_tag_name('button')
        premise_toggle_button.click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'mat-drawer-inner-container')))
        mat_drawer_inner_container = driver.find_element_by_class_name('mat-drawer-inner-container')
        scroller_header = mat_drawer_inner_container.find_element_by_class_name('scroller-header')
        expansion_button = scroller_header.find_element_by_tag_name('button')
        expansion_button.click()
        
        time.sleep(2)
        #Check here for the length of expansion panel, if it is more than one, then there are companies and facilities are split according to that, have to look into that
        mat_expansion_panel_body = mat_drawer_inner_container.find_elements_by_class_name('mat-expansion-panel-body')[-1]
        mat_cards = mat_expansion_panel_body.find_elements_by_tag_name('mat-card')
        if index >= len(mat_cards):
            break
        # if quantity == "ENERGY" or index == 0:
        #     i = index - 1
        #     while(i>=0):
        #         curr_mat_card = mat_cards[i]
        #         curr_mat_checkbox = curr_mat_card.find_element_by_class_name('mat-checkbox-inner-container')
        #         driver.execute_script("arguments[0].click();",curr_mat_checkbox)
        #         # curr_mat_checkbox.click()
        #         i -= 1
        scroller_footer = mat_drawer_inner_container.find_element_by_class_name('scroller-footer')
        clear_all_button = scroller_footer.find_element_by_tag_name('button')
        clear_all_button.click()
        time.sleep(1)
        mat_drawer_inner_container = driver.find_element_by_class_name('mat-drawer-inner-container')
        mat_expansion_panel_body = mat_drawer_inner_container.find_elements_by_class_name('mat-expansion-panel-body')[-1]
        mat_cards = mat_expansion_panel_body.find_elements_by_tag_name('mat-card')
        curr_mat_card = mat_cards[index]
        kind = 'Fjärrvärme'
        curr_mat_checkbox = curr_mat_card.find_element_by_class_name('mat-checkbox-inner-container')
        driver.execute_script("arguments[0].click();",curr_mat_checkbox)
        time.sleep(1)
        mat_drawer_inner_container = driver.find_element_by_class_name('mat-drawer-inner-container')
        mat_expansion_panel_body = mat_drawer_inner_container.find_elements_by_class_name('mat-expansion-panel-body')[-1]
        mat_cards = mat_expansion_panel_body.find_elements_by_tag_name('mat-card')
        curr_mat_card = mat_cards[index]
        facilityId = curr_mat_card.find_element_by_class_name('id-section').text
        # curr_mat_checkbox.click()
        print(facilityId,kind)
        premise_toggle_button.click()
        time.sleep(1)
        wait.until(EC.invisibility_of_element((By.CLASS_NAME,"loading-wrapper")))
        date_group = driver.find_element_by_class_name('date-group')
        mat_buttons_toggle = date_group.find_elements_by_tag_name('mat-button-toggle')
        resolution_button = mat_buttons_toggle[-1]
        selected_resolution = resolution_button.text
        resolution_button.click()
        time.sleep(5)
        # wait.until(EC.invisibility_of_element((By.CLASS_NAME,"loading-wrapper")))
        date_picker = driver.find_element_by_class_name('date-picker')
        from_date_input = date_picker.find_element_by_class_name('mat-input-element')
        from_date_input.clear()
        from_date_input.send_keys('2020-01-01')
        from_date_input.send_keys(Keys.RETURN)
        time.sleep(5)
        export_button = driver.find_element_by_id('button-exportdata')
        export_button.click()
        has_downloaded = False
        download_sleep_count = 0
        while(not has_downloaded and download_sleep_count < 30):
            # print('Now waiting in download')
            if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-4:] == 'xlsx' and download_sleep_count < 30 :
                has_downloaded = True
            time.sleep(1)
            download_sleep_count += 1
        if download_sleep_count < 30:
            complete_data_block = prepare_data(download_dir, facilityId, kind, selected_resolution, quantity)
            log.data(complete_data_block)
            log.info('Indexed data with facilityId {0}'.format(facilityId))
        else:
            log.info('Download failed for facilityId {0}'.format(facilityId))
        index += 1

def VattenfallHeating(agentRunContext):

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
        wait = WebDriverWait(driver, 150)
        try:
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'app-cookies')))
            app_cookies = driver.find_element_by_class_name('app-cookies')
            accept_button = app_cookies.find_element_by_tag_name('button')
            accept_button.click()
            time.sleep(1)
        except TimeoutException:
            log.job(config.JOB_RUNNING_STATUS,"No cookies")
        info_block = driver.find_element_by_class_name('info-block')
        a_tags = info_block.find_elements_by_tag_name('a')
        for a_tag in a_tags:
            if 'Logga in' in a_tag.text:
                a_tag.click()
                time.sleep(2)
                break
        wait.until(EC.element_to_be_clickable((By.ID,'usernameInput')))
        driver.find_element_by_id('usernameInput').send_keys(agentRunContext.requestBody['username'])
        driver.find_element_by_id('password').send_keys(agentRunContext.requestBody['password'])
        login_button = driver.find_element_by_class_name('btn')
        login_button.click()
        time.sleep(1)
        try:
            wait.until(EC.invisibility_of_element((By.CLASS_NAME,"loading-wrapper")))
            wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'left-nav-content')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to login, invalid username or password')
            driver.close()
            os.rmdir(download_dir)
            return
        #Loop should be brought in here
        # print("Getting all facilityIds")
        # driver.execute_script("window.location.href = '/mina-sidor/contract';")
        # wait.until(EC.invisibility_of_element((By.CLASS_NAME,"loading-wrapper")))
        # wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'page-layout')))
        # premise_toggle = driver.find_element_by_class_name('premise-toggle')
        # premise_toggle_button = premise_toggle.find_element_by_tag_name('button')
        # premise_toggle_button.click()
        # time.sleep(1)
        # wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'mat-drawer-inner-container')))
        # mat_drawer_inner_container = driver.find_element_by_class_name('mat-drawer-inner-container')
        # facilities_mat_expansion_panel = mat_drawer_inner_container.find_elements_by_class_name('mat-expansion-panel')[-1]
        # mat_expansion_panel_content = facilities_mat_expansion_panel.find_element_by_class_name('mat-expansion-panel-content')
        # mat_cards = mat_expansion_panel_content.find_elements_by_class_name('mat-card')
        # address_id_ds = {}
        # driver.execute_script("documet.getElementsByClassName('mat-drawer-inner-container').scrollTo(0,);'")
        # for facility in mat_cards:
        #     facility_label = facility.find_element_by_class_name('mat-checkbox-label').text
        #     check_box = facility.find_element_by_class_name('mat-checkbox-input')
        #     check_box.click()
        #     time.sleep(1.5)
        #     facilityId = driver.find_element_by_class_name('contract-value').text
        #     address_id_ds[facility_label] = facilityId
        # print(address_id_ds)
        driver.execute_script("window.location.href = '/mina-sidor/report/consumption'")
        print('Now handling energy')
        wait.until(EC.invisibility_of_element((By.CLASS_NAME,"loading-wrapper")))
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'left-nav-content')))
        select_and_download_data(wait, driver, log, download_dir, 'ENERGY')
        time.sleep(2)
        driver.execute_script("window.location.href = '/mina-sidor/report/flow'")
        print('Now handling volume')
        wait.until(EC.invisibility_of_element((By.CLASS_NAME,"loading-wrapper")))
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'left-nav-content')))
        select_and_download_data(wait, driver, log, download_dir, 'VOLUME')
        time.sleep(2)
        driver.execute_script("window.location.href = '/mina-sidor/report/effect'")
        print('Now handling effect')
        wait.until(EC.invisibility_of_element((By.CLASS_NAME,"loading-wrapper")))
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'left-nav-content')))
        select_and_download_data(wait, driver, log, download_dir, 'POWER')
        time.sleep(2)
        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,"Successfully scraped data for all available facilities")
        

    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())
    
    driver.close()
    os.rmdir(download_dir)