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
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from calendar import monthrange


from common import get_driver
from common import Log
import config

def prepare_data(download_dir,facilityId,kind,unit,resolution,quantity):
    complete_data_block = []
    for f in os.listdir(download_dir):
        df = pd.read_excel(os.path.join(download_dir,os.listdir(download_dir)[0]),names=['date','consumption'])
        for j in range(len(df)):
            if pd.notna(df['date'][j]) and pd.notna(df['consumption'][j]):
                start_date = parse(df['date'][j])
                if resolution == 'Timme':
                    end_date = start_date + relativedelta(hours=1)
                if resolution == 'Dag':
                    end_date = start_date + relativedelta(days=1)
                if resolution == 'Månad':
                    end_date = start_date + relativedelta(days=monthrange(start_date.year, start_date.month)[1] - 1)
                if resolution == 'År':
                    end_date = start_date + relativedelta(years=1)
                if quantity == "Energi":
                    q = 'ENERGY'
                if quantity == 'Flöde':
                    q = 'VOLUME'
                if quantity == 'Delta-T':
                    q = 'TEMPERATURE'
                complete_data_block.append({'facilityId':facilityId,'kind':kind,'unit':unit,'quantity':q,'startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['consumption'][j]})
        os.remove(os.path.join(download_dir,f))
        # time.sleep(1)
        # print('Hrererrrrerere',os.listdir(download_dir))
        return complete_data_block

def prepare_data_el(download_dir,facilityId,year):
    for f in os.listdir(download_dir):
        wb = load_workbook(os.path.join(download_dir,f),data_only=True)
        sheet_ranges = wb['Serie']
        start_let = 76
        offset = 0
        index = 3
        start_date = dt(year,1,1,0,0,0)
        complete_data_block = []
        for i in range(1,13):
            index = 3
            curr_al = start_let + offset
            # print(chr(curr_al)+''+str(index))
            while(sheet_ranges[chr(curr_al)+''+str(index)].value != None):
                end_date = start_date + relativedelta(hours=1)
                complete_data_block.append({'facilityId':facilityId,'kind':'El','quantity':'ENERGY','unit':'kWh','startDate':dt.strftime(start_date,"%Y-%m-%d %H:%M:%S"),'endDate':dt.strftime(end_date,"%Y-%m-%d %H:%M:%S"),'value':sheet_ranges[chr(curr_al)+''+str(index)].value})
                index += 1
                start_date = start_date + relativedelta(hours=1)
            offset += 1
        os.remove(os.path.join(download_dir,f))
        # print(complete_data_block[:10])
        return complete_data_block

def download_heat_cool(driver,download_dir,wait,facilityId,kind,log):
    consumption_heat_category_dropdown = driver.find_element_by_tag_name('consumption-heat-category-dropdown')
    show_graph_choice = consumption_heat_category_dropdown.find_element_by_class_name('consumption-filter-block-item')
    btn_dropdown = show_graph_choice.find_element_by_class_name('btn-dropdown')
    btn = btn_dropdown.find_element_by_class_name('btn')
    graph_options_ul = btn_dropdown.find_element_by_class_name('dropdown-menu')
    graph_options_li_tags = graph_options_ul.find_elements_by_tag_name('li')
    graph_options_li_tags_range = len(graph_options_li_tags)
    orientation = 0
    for i in range(graph_options_li_tags_range):
        driver.execute_script("if(document.getElementsByClassName('_hj-widget-container')[0] != undefined){document.getElementsByClassName('_hj-widget-container')[0].style.display = 'none';}")
        time.sleep(2)
        consumption_heat_category_dropdown = driver.find_element_by_tag_name('consumption-heat-category-dropdown')
        show_graph_choice = consumption_heat_category_dropdown.find_element_by_class_name('consumption-filter-block-item')
        btn_dropdown = show_graph_choice.find_element_by_class_name('btn-dropdown')
        btn = btn_dropdown.find_element_by_class_name('btn')
        graph_options_ul = btn_dropdown.find_element_by_class_name('dropdown-menu')
        graph_options_li_tags = graph_options_ul.find_elements_by_tag_name('li')
        graph_option_li = graph_options_li_tags[i]
        li_choice_a = graph_option_li.find_element_by_tag_name('a')
        if i == 0 or i == 1 or i == 5:
            btn = btn_dropdown.find_element_by_class_name('btn')
            btn.click()
            quantity = li_choice_a.text
            if i==0:
                quantity = 'Energi'
                unit = 'kWh'
            if i==1:
                quantity = 'Flöde'
                unit = 'm3'
            if i==5:
                quantity = 'Delta-T'
                unit = 'C'
            driver.execute_script("window.scrollTo(0,350);")
            time.sleep(1.5)
            li_choice_a.click()
            time.sleep(2)
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'highchart-loading')))
            consumption_filter_time = driver.find_element_by_tag_name('consumption-filter-time')
            resolution_block = consumption_filter_time.find_element_by_class_name('consumption-filter-block-item')
            resolution_block_dropdown = resolution_block.find_element_by_class_name('btn-dropdown')
            resolution_block_button = resolution_block_dropdown.find_element_by_class_name('btn')
            resolution_block_button.click()
            time.sleep(1.5)
            resolution_block_dropdown_menu = resolution_block_dropdown.find_element_by_class_name('dropdown-menu')
            first_resolution_option = resolution_block_dropdown_menu.find_element_by_tag_name('li').find_element_by_tag_name('a')
            resolution = first_resolution_option.text
            first_resolution_option.click()
            time.sleep(2)
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'highchart-loading')))
            from_date_picker = consumption_filter_time.find_elements_by_tag_name('datepicker-dropdown')[0]
            to_date_picker = consumption_filter_time.find_elements_by_tag_name('datepicker-dropdown')[1]
            from_date_picker_input = from_date_picker.find_element_by_tag_name('input')
            from_date_picker_input.click()
            time.sleep(1.5)
            starting_month = 'januari 2020'
            driver.execute_script("window.scrollTo(0,150);")
            time.sleep(2)
            from_date_picker_ul = from_date_picker.find_element_by_class_name('uib-datepicker-popup')
            from_date_picker_table = from_date_picker_ul.find_element_by_tag_name('table')
            from_date_picker_table_thead = from_date_picker_table.find_element_by_tag_name('thead')
            thead_tr = from_date_picker_table_thead.find_element_by_tag_name('tr')
            thead_ths = thead_tr.find_elements_by_tag_name('th')
            while(thead_ths[1].text != starting_month):
                thead_ths[0].find_element_by_tag_name('button').click()
            from_date_picker_table_tbody = from_date_picker_table.find_element_by_tag_name('tbody')
            from_date_picker_days = from_date_picker_table_tbody.find_elements_by_class_name('uib-day')
            for day in from_date_picker_days:
                if day.text == "01":
                    day.find_element_by_tag_name('button').click()
                    break
            time.sleep(2)
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'highchart-loading')))
            driver.execute_script("window.scrollTo(0,1000);")
            time.sleep(2)
            consumption_graph_container = driver.find_element_by_id('consumption-graph-container')
            highcharts_subtitle = consumption_graph_container.find_element_by_class_name('highcharts-subtitle')
            previous_link = consumption_graph_container.find_element_by_class_name('link-previous')
            next_link = consumption_graph_container.find_element_by_class_name('link-next')
            download_button = consumption_graph_container.find_element_by_tag_name('button')
            data_count = 0
            while(data_count <= 3):
                download_button.click()
                time.sleep(2)
                has_downloaded = False
                download_sleep_count = 0
                while(not has_downloaded and download_sleep_count < 35):
                    # print('Now waiting in download')
                    if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-4:] == 'xlsx' and download_sleep_count < 35 :
                        has_downloaded = True
                        # print(os.listdir(download_dir))
                        time.sleep(1)
                    time.sleep(1)
                    download_sleep_count += 1
                                # print(download_sleep_count)
                if download_sleep_count < 35:
                    complete_data_block = prepare_data(download_dir,facilityId,kind,unit,resolution,quantity)
                    log.data(complete_data_block)
                    # print(len(complete_data_block))
                    log.info('Indexed data for facilityId {0}, count {1}, quantity {2}, len {3}'.format(facilityId,data_count,quantity,len(complete_data_block)))
                else:
                    print('Unable to load data for {0}, count {1}, quantity {2}'.format(facilityId,data_count,quantity))
                    log.info('Unable to load data for {0}, count {1}, quantity {2}'.format(facilityId,data_count,quantity))
                if 'disabled' not in next_link.get_attribute('class'):
                    driver.execute_script("if(document.getElementsByClassName('_hj-widget-container')[0] != undefined){document.getElementsByClassName('_hj-widget-container')[0].style.display = 'none';}")
                    time.sleep(1)
                    next_link.click()
                else:
                    break
                time.sleep(2)
                wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'highchart-loading')))
                data_count += 1
            orientation += 1
            driver.execute_script("window.scrollTo(0,250);")
            time.sleep(2)

# def download_el_second(download_dir,driver,wait,facilityId,log):

def download_el(download_dir,driver,wait,facilityId,log,ver):
    months = {'January':'Januari','February':'Februari','March':'Mars','April':'April','May':'Maj','June':'Juni','July':'Juli','August':'Augusti','September':'September','October':'Oktober','November':'November','December':'December'}
    driver.execute_script("window.scrollTo(0,400);")
    time.sleep(2)
    resolution_btn_group = driver.find_elements_by_class_name('btn-group')[-1]
    resolution_button = resolution_btn_group.find_elements_by_tag_name('button')[0]
    el_resolution = resolution_button.text
    if el_resolution == 'År':
        return
    resolution_button.click()
    # time.sleep(1)
    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'highchart-loading')))
    # from_date_select_el = driver.find_elements_by_class_name('input_container')[0]
    # to_date_select_el = driver.find_elements_by_class_name('input_container')[1]
    # # driver.execute_script("document.getElementsByClassName('input_container')[0].getElementsByTagName('input')[0].readOnly = false;document.getElementsByClassName('input_container')[1].getElementsByTagName('input')[0].readOnly = false;")
    # time.sleep(1)
    # if ver == 1:
    #     start_date = dt(dt.now().year,1,1)
    #     while(1):
    #         driver.execute_script("if(document.getElementsByClassName('_hj-widget-container')[0] != undefined){document.getElementsByClassName('_hj-widget-container')[0].style.display = 'none';}")
    #         time.sleep(2)
    #         end_date = start_date + relativedelta(days=30)
    #         from_date_select_el = driver.find_elements_by_class_name('input_container')[0]
    #         to_date_select_el = driver.find_elements_by_class_name('input_container')[1]
    #         to_date_select_el_input = to_date_select_el.find_element_by_tag_name('input')
    #         to_date_select_el_input.clear()
    #         from_date_select_el_input = from_date_select_el.find_element_by_tag_name('input')
    #         from_date_select_el_input.clear()
    #         from_date_select_el_input.send_keys(dt.strftime(start_date,"%Y-%m-%d"))
    #         from_date_select_el_input.send_keys(Keys.RETURN)
    #         time.sleep(2)
    #         to_date_select_el_input.send_keys(dt.strftime(end_date,"%Y-%m-%d"))
    #         to_date_select_el_input.send_keys(Keys.RETURN)
    #         time.sleep(2)
    #         driver.execute_script("window.scrollTo(0,1000);")
    #         time.sleep(2)
    #         wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
    #         year_el_download_button = driver.find_element_by_class_name('mart20').find_element_by_class_name('btn')
    #         year_el_download_button.click()
    #         time.sleep(2)
    #         wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'spinner')))
    #         has_downloaded = False
    #         download_sleep_count = 0
    #         while(not has_downloaded and download_sleep_count < 25):
    #             # print('Now waiting in download')
    #             if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-4:] == 'xlsx' and download_sleep_count < 25 :
    #                 has_downloaded = True
    #             time.sleep(1)
    #             download_sleep_count += 1
    #         if download_sleep_count < 25:
    #             complete_data_block = prepare_data_el(download_dir,facilityId,start_date.year)
    #             log.data(complete_data_block)
    #             log.info('Indexed data for facilityId {0}, year {1}'.format(facilityId,start_date.year))
    #         else:
    #             print('Unable to load data')
    #             log.info('Unable to load data for facilityId {0}, year {1}'.format(facilityId,start_date.year))
    #         driver.execute_script("window.scrollTo(0,250)")
    #         time.sleep(2)
    #         start_date = start_date - relativedelta(years=1)
    #         if start_date.year == 2018:
    #                 # print('Here in break')
    #             break
    # elif ver == 2:
    start_date = dt(dt.now().year,dt.now().month,1)
    # start_date = dt(2020,7,1)
    while(1):
        end_date = dt(start_date.year,start_date.month,monthrange(start_date.year,start_date.month)[1])
        # print(end_date,end_date>dt.now())
        if end_date > dt.now():
            end_date = dt(start_date.year,start_date.month,dt.now().day)
        driver.execute_script("if(document.getElementsByClassName('_hj-widget-container')[0] != undefined){document.getElementsByClassName('_hj-widget-container')[0].style.display = 'none';}")
        # time.sleep(2)
        from_date_select_el = driver.find_elements_by_class_name('input_container')[0]
        # to_date_select_el_input.clear()
        from_date_select_el_input = from_date_select_el.find_element_by_tag_name('input')
        from_date_select_el_input.click()
        driver.execute_script("if(document.getElementsByClassName('_hj-widget-container')[0] != undefined){document.getElementsByClassName('_hj-widget-container')[0].style.display = 'none';}")
        # time.sleep(2)
        if el_resolution == 'Månad':
            datepicker_class = driver.find_element_by_class_name('datepicker-months')
            calendar_table = datepicker_class.find_element_by_tag_name('table')
            prev_th = calendar_table.find_element_by_class_name('prev')
            curr_selected_year = calendar_table.find_element_by_class_name('datepicker-switch')
            max_from_reached = False
            while(curr_selected_year.text != str(start_date.year)):
                if 'visibility: hidden' in prev_th.get_attribute('style'):
                    max_from_reached = True
                    print('Here inside break')
                    break
                prev_th.click()
            if max_from_reached:
                driver.execute_script("window.scrollTo(0,250);")
                time.sleep(2)
                break
            calendar_months = calendar_table.find_elements_by_class_name('month')
            for calendar_month in calendar_months:
                if calendar_month.text == months[dt.strftime(start_date,'%B')][:3]:
                    calendar_month.click()
                    break
            to_date_select_el = driver.find_elements_by_class_name('input_container')[1]
            to_date_select_el_input = to_date_select_el.find_element_by_tag_name('input')
            to_date_select_el_input.click()
            datepicker_class = driver.find_element_by_class_name('datepicker-months')
            calendar_table = datepicker_class.find_element_by_tag_name('table')
            prev_th = calendar_table.find_element_by_class_name('prev')
            curr_selected_year = calendar_table.find_element_by_class_name('datepicker-switch')
            driver.execute_script("if(document.getElementsByClassName('_hj-widget-container')[0] != undefined){document.getElementsByClassName('_hj-widget-container')[0].style.display = 'none';}")
            # time.sleep(2)
            max_to_reached = False
            while(curr_selected_year.text != str(start_date.year)):
                if 'visibility: hidden' in prev_th.get_attribute('style'):
                    max_to_reached = True
                    print('Here inside break')
                    break
                prev_th.click()
            if max_to_reached:
                driver.execute_script("window.scrollTo(0,250);")
                time.sleep(2)
                break
            calendar_months = calendar_table.find_elements_by_class_name('month')
            for calendar_month in calendar_months:
                if calendar_month.text == months[dt.strftime(start_date,'%B')][:3]:
                    calendar_month.click()
                    break
        else:
            datepicker_class = driver.find_element_by_class_name('datepicker')
            calendar_table = datepicker_class.find_element_by_tag_name('table')
            prev_th = calendar_table.find_element_by_class_name('prev')
            curr_selected_month = calendar_table.find_element_by_class_name('datepicker-switch')
            max_from_reached = False
            while(curr_selected_month.text != months[dt.strftime(start_date,'%B')]+' '+str(start_date.year)):
                if 'visibility: hidden' in prev_th.get_attribute('style'):
                    max_from_reached = True
                    print('Here inside break')
                    break
                prev_th.click()
            if max_from_reached:
                driver.execute_script("window.scrollTo(0,250);")
                time.sleep(2)
                break
            calendar_days = calendar_table.find_elements_by_class_name('day')
            for calendar_day in calendar_days:
                if calendar_day.text == str(start_date.day) and 'old' not in calendar_day.get_attribute('class'):
                    calendar_day.click()
                    break
            to_date_select_el = driver.find_elements_by_class_name('input_container')[1]
            to_date_select_el_input = to_date_select_el.find_element_by_tag_name('input')
            to_date_select_el_input.click()
            datepicker_class = driver.find_element_by_class_name('datepicker')
            calendar_table = datepicker_class.find_element_by_tag_name('table')
            prev_th = calendar_table.find_element_by_class_name('prev')
            curr_selected_month = calendar_table.find_element_by_class_name('datepicker-switch')
            driver.execute_script("if(document.getElementsByClassName('_hj-widget-container')[0] != undefined){document.getElementsByClassName('_hj-widget-container')[0].style.display = 'none';}")
            # time.sleep(2)
            max_to_reached = False
            while(curr_selected_month.text != months[dt.strftime(end_date,'%B')]+' '+str(end_date.year)):
                if 'visibility: hidden' in prev_th.get_attribute('style'):
                    max_to_reached = True
                    break
                prev_th.click()
            if max_to_reached:
                driver.execute_script("window.scrollTo(0,250);")
                time.sleep(2)
                break
            calendar_days = calendar_table.find_elements_by_class_name('day')
            for calendar_day in calendar_days:
                if calendar_day.text == str(end_date.day) and 'old' not in calendar_day.get_attribute('class'):
                    calendar_day.click()
                    break
        # from_date_select_el_input.clear()
        # from_date_select_el_input.send_keys(dt.strftime(start_date,"%Y-%m-%d"))
        # from_date_select_el_input.send_keys(Keys.RETURN)
        # time.sleep(2)
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'highchart-loading')))
        time.sleep(2)
        # time.sleep(2)
        # to_date_select_el_input.send_keys(dt.strftime(end_date,"%Y-%m-%d"))
        # to_date_select_el_input.send_keys(Keys.RETURN)
        # time.sleep(2)
        driver.execute_script("window.scrollTo(0,1000);")
        time.sleep(2)
        # wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'highchart-loading')))
        # time.sleep(2)
        try:
            WebDriverWait(driver, 25).until(EC.element_to_be_clickable((By.CLASS_NAME,'next_button')))
        except TimeoutException:
            log.info('No data available for facilityId {0} for the period {1}--{2}'.format(facilityId,dt.strftime(start_date,"%Y-%m-%d"),dt.strftime(end_date,"%Y-%m-%d")))
            start_date = start_date - relativedelta(months=1)
            if start_date.year < 2020:
                driver.execute_script("window.scrollTo(0,250);")
                time.sleep(2)
                break
            driver.execute_script("window.scrollTo(0,400);")
            time.sleep(2)
            continue
        # time.sleep(1)
        try:
            download_excel_el_button = driver.find_element_by_class_name('graph-container').find_element_by_class_name('btn')
        except NoSuchElementException:
            driver.execute_script("window.scrollTo(0,400);")
            time.sleep(2)
            start_date = start_date - relativedelta(months=1)
            if start_date.year < 2020:
                driver.execute_script("window.scrollTo(0,250);")
                time.sleep(2)
                break
            continue

        download_excel_el_button.click()
        # time.sleep(2)
        has_downloaded = False
        download_sleep_count = 0
        while(not has_downloaded and download_sleep_count < 30):
            # print('Now waiting in download')
            if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-4:] == 'xlsx' and download_sleep_count < 30 :
                has_downloaded = True
                # print(os.listdir(download_dir))
                # time.sleep(2)
            time.sleep(1)
            download_sleep_count += 1
                # print(download_sleep_count)
        if download_sleep_count < 30:
            complete_data_block = prepare_data(download_dir,facilityId,'El','kWh',el_resolution,'Energi')
                        # print(complete_data_block[:10])
            log.data(complete_data_block)
            # print(len(complete_data_block))
            log.info('Indexed data for facilityId {0} with period {1}--{2}, len {3}'.format(facilityId,dt.strftime(start_date,"%Y-%m-%d"),dt.strftime(end_date,"%Y-%m-%d"),len(complete_data_block)))
        else:
            print('Download failed')
            log.info('Download failed for {0} with period {1}--{2}'.format(facilityId,dt.strftime(start_date,"%Y-%m-%d"),dt.strftime(end_date,"%Y-%m-%d")))
        driver.execute_script("window.scrollTo(0,400);")
        time.sleep(2)
        start_date = start_date - relativedelta(months=1)
        if start_date.year < 2020:
            driver.execute_script("window.scrollTo(0,250);")
            time.sleep(2)
            break

def Vattenfall(agentRunContext):

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
        #document.getElementById('cmpwelcomebtnyes').getElementsByTagName('a')[0].click()
        try:
            wait.until(EC.element_to_be_clickable((By.ID,'cmpwelcomebtnyes')))
            driver.execute_script("document.getElementById('cmpwelcomebtnyes').getElementsByTagName('a')[0].click()")
            time.sleep(2)
            wait.until(EC.invisibility_of_element((By.ID,'cmpbox2')))
        except TimeoutException:
            log.job(config.JOB_RUNNING_STATUS,'No cookies shown')
            # driver.close()
            # os.rmdir(download_dir)
            # return
        #document.getElementsByClassName('login-dropdown')[0].getElementsByTagName('a')[0].click() nav-login
        driver.find_element_by_class_name('login-dropdown').find_element_by_tag_name('a').click()
        time.sleep(1)
        wait.until(EC.visibility_of_element_located((By.ID,'nav-login')))
        nav_login = driver.find_element_by_id('nav-login')
        login_types = nav_login.find_elements_by_tag_name('a')
        for login_type in login_types:
            if login_type.get_attribute('title') == 'Privat':
                login_type.click()
                break
        wait.until(EC.element_to_be_clickable((By.ID,'customerNumTab')))
        driver.find_element_by_id('customerNumTab').click()
        time.sleep(2)
        wait.until(EC.element_to_be_clickable((By.ID,'customerId')))
        driver.execute_script("document.getElementById('customerId').value = '{0}';document.getElementById('pin').value = '{1}';document.getElementById('submitButton2').click();".format(agentRunContext.requestBody['username'],agentRunContext.requestBody['password']))
        time.sleep(2)
        try:
            wait.until(EC.visibility_of_element_located((By.ID,'navbar')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to login, invalid username or password')
            driver.close()
            os.rmdir(download_dir)
            return
        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')
        driver.execute_script("window.location.href = '/foretag/mina-sidor/min-forbrukning/'")
        time.sleep(2)
        #Write the code here for v1 using try and catch, in exception handle for V2
        try:
            WebDriverWait(driver, 7).until(EC.visibility_of_element_located((By.CLASS_NAME,"slick-track")))
            log.info('This user is V1')
            print('This user is V1')
            ver = 1
            slick_track = driver.find_element_by_class_name('slick-track')
            slick_slides = slick_track.find_elements_by_class_name('slick-slide')
            facilities = []
            kind_lookup = {'heat-1.svg':'Fjärrvärme','heat-2.svg':'Fjärrvärme','Cool-1.svg':'Fjärrkyla','el-1.svg':'El','el-2.svg':'El'}
            for i,slick_slide in enumerate(slick_slides):
                curr_div = slick_slide.find_elements_by_tag_name('div')[1]
                img_src = os.path.basename(curr_div.find_element_by_class_name('premise-avtar').find_element_by_tag_name('img').get_attribute('src')).lower()
                if 'heat' in img_src:
                    kind = 'Fjärrvärme'
                if 'cool' in img_src:
                    kind = 'Fjärrkyla'
                if 'el' in img_src:
                    kind = 'El'
                facilities.append((curr_div.get_attribute('id'),kind))
            log.job(config.JOB_RUNNING_STATUS,'Started scraping data')
            for facility in facilities:
                facilityId = facility[0]
                kind = facility[1]
                print(facilityId,kind)
                driver.execute_script("window.onPremiseElementSelect(document.getElementById('{0}'))".format(facilityId))
                time.sleep(2)
                wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
                if kind == 'Fjärrvärme' or kind == 'Fjärrkyla':
                    download_heat_cool(driver, download_dir, wait, facilityId, kind, log)
                elif kind == 'El':
                    download_el(download_dir, driver, wait, facilityId, log, ver)
        except TimeoutException:
            log.info('This user is V2')
            print('This user is V2')
            ver = 2
            try:
                premise_desktop_toggle = driver.find_element_by_class_name("premise-desktop__toggle")
            except NoSuchElementException:
                log.job(config.JOB_COMPLETED_FAILED_STATUS,"Not able to get facilityId")
                driver.close()
                os.rmdir(download_dir)
                return()
            premise_button = premise_desktop_toggle.find_element_by_class_name('btn')
            premise_button.click()
            time.sleep(2)
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME,"select-menu__container")))
            facility_select_menu = driver.find_element_by_class_name('select-menu__container')
            facility_table = facility_select_menu.find_element_by_tag_name('table')
            facility_table_tbody = facility_table.find_element_by_tag_name('tbody')
            facilities = facility_table_tbody.find_elements_by_tag_name('tr')
            log.job(config.JOB_RUNNING_STATUS,'Started scraping data')
            x = 20
            for i in range(len(facilities)):
                div_scroller = driver.find_element_by_class_name('scroller')
                driver.execute_script("arguments[0].scrollTo(0,{0});".format(x),div_scroller)
                x += 20
                x_scrollbar = div_scroller.find_element_by_class_name('ps-scrollbar-x-rail')
                driver.execute_script("arguments[0].style.display = 'none';",x_scrollbar)
                facility_select_menu = driver.find_element_by_class_name('select-menu__container')
                facility_table = facility_select_menu.find_element_by_tag_name('table')
                facility_table_tbody = facility_table.find_element_by_tag_name('tbody')
                facilities = facility_table_tbody.find_elements_by_tag_name('tr')
                facility = facilities[i]
                facilityId = facility.find_elements_by_tag_name('td')[0].text
                kind = facility.find_elements_by_tag_name('td')[-1].text
                print(facilityId,kind)
                log.info('facilityId {0}, kind {1}'.format(facilityId,kind))
                facility.click()
                time.sleep(2)
                wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
                close_div = driver.find_element_by_class_name('select-menu__header-header')
                close_button = close_div.find_element_by_class_name('btn')
                close_button.click()
                if kind == 'Fjärrvärme' or kind == 'Fjärrkyla':
                    download_heat_cool(driver, download_dir, wait, facilityId, kind, log)
                elif kind == 'El':
                    download_el(download_dir, driver, wait, facilityId, log, ver) 
                # time.sleep(2)
                premise_button.click()
                time.sleep(2)
                wait.until(EC.visibility_of_element_located((By.CLASS_NAME,"select-menu__container")))
        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,"Successfully scraped data for all available facilities")
    
    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())
    
    driver.close()
    os.rmdir(download_dir)