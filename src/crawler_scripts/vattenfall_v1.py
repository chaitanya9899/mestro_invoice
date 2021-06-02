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
        df = pd.read_excel(os.path.join(download_dir,f),names=['date','consumption'])
        for j in range(len(df)):
            if pd.notna(df['date'][j]) and pd.notna(df['consumption'][j]):
                end_date = parse(df['date'][j])
                if resolution == 'Timme':
                    start_date = end_date - relativedelta(hours=1)
                if resolution == 'Dag':
                    start_date = end_date - relativedelta(days=1)
                if resolution == 'Månad':
                    start_date = end_date - relativedelta(months=1)
                if resolution == 'År':
                    start_date = end_date - relativedelta(years=1)
                if quantity == "Energi":
                    q = 'ENERGY'
                if quantity == 'Flöde':
                    q = 'VOLUME'
                if quantity == 'Delta-T':
                    q = 'TEMPERATURE'
                complete_data_block.append({'facilityId':facilityId,'kind':kind,'unit':unit,'quantity':q,'startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['consumption'][j]})
        os.remove(os.path.join(download_dir,f))
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

def VattenfallV1(agentRunContext):

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
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Not able to load the website')
            driver.close()
            os.rmdir(download_dir)
            return
        
        driver.execute_script("document.getElementById('cmpwelcomebtnyes').getElementsByTagName('a')[0].click()")

        time.sleep(2)

        wait.until(EC.invisibility_of_element((By.ID,'cmpbox2')))

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

        wait.until(EC.visibility_of_element_located((By.CLASS_NAME,"slick-track")))

        slick_track = driver.find_element_by_class_name('slick-track')

        slick_slides = slick_track.find_elements_by_class_name('slick-slide')

        facilities = []

        kind_lookup = {'heat-1.svg':'Fjärrvärme','heat-2.svg':'Fjärrvärme','Cool-1.svg':'Fjärrkyla','el-1.svg':'El','el-2.svg':'El'}

        for slick_slide in slick_slides:
            curr_div = slick_slide.find_elements_by_tag_name('div')[1]
            facilities.append((curr_div.get_attribute('id'),kind_lookup[os.path.basename(curr_div.find_element_by_class_name('premise-avtar').find_element_by_tag_name('img').get_attribute('src'))]))
        
        # print(facilities)

        log.job(config.JOB_RUNNING_STATUS,'Started scraping data')
        
        for facility in facilities:
            facilityId = facility[0]
            kind = facility[1]
            # print('Selecting id {0}'.format(facilityId))
            driver.execute_script("window.onPremiseElementSelect(document.getElementById('{0}'))".format(facilityId))
            time.sleep(2)
            # driver.execute_script("window.scrollTo(0,0);")
            wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
            # time.sleep(2)

            #Here check facility type

            if kind == 'Fjärrvärme' or kind == 'Fjärrkyla':
                #Selecting stuff is different here
                consumption_heat_category_dropdown = driver.find_element_by_tag_name('consumption-heat-category-dropdown')
                show_graph_choice = consumption_heat_category_dropdown.find_element_by_class_name('consumption-filter-block-item')
                btn_dropdown = show_graph_choice.find_element_by_class_name('btn-dropdown')
                btn = btn_dropdown.find_element_by_class_name('btn')
                graph_options_ul = btn_dropdown.find_element_by_class_name('dropdown-menu')
                graph_options_li_tags = graph_options_ul.find_elements_by_tag_name('li')
                graph_options_li_tags_range = len(graph_options_li_tags)
                orientation = 0
                for i in range(graph_options_li_tags_range):
                    consumption_heat_category_dropdown = driver.find_element_by_tag_name('consumption-heat-category-dropdown')
                    show_graph_choice = consumption_heat_category_dropdown.find_element_by_class_name('consumption-filter-block-item')
                    btn_dropdown = show_graph_choice.find_element_by_class_name('btn-dropdown')
                    btn = btn_dropdown.find_element_by_class_name('btn')
                    graph_options_ul = btn_dropdown.find_element_by_class_name('dropdown-menu')
                    graph_options_li_tags = graph_options_ul.find_elements_by_tag_name('li')
                    # btn = btn_dropdown.find_element_by_class_name('btn')
                    # btn.click()
                    graph_option_li = graph_options_li_tags[i]
                    li_choice_a = graph_option_li.find_element_by_tag_name('a')
                    # print(li_choice_a.text)
                    if i == 0 or i == 1 or i == 5:
                        btn = btn_dropdown.find_element_by_class_name('btn')
                        btn.click()
                        # print('Selected {0}'.format(li_choice_a.text),i)
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
                        driver.execute_script("window.scrollTo(0,250);")
                        time.sleep(1.5)
                        li_choice_a.click()
                        time.sleep(2)
                        wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
                        #Here we will have loop and extra stuff for period selection and such
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
                        wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
                        # print('Selected resolution is {0}'.format(resolution))
                        from_date_picker = consumption_filter_time.find_elements_by_tag_name('datepicker-dropdown')[0]
                        to_date_picker = consumption_filter_time.find_elements_by_tag_name('datepicker-dropdown')[1]
                        from_date_picker_input = from_date_picker.find_element_by_tag_name('input')
                        from_date_picker_input.click()
                        time.sleep(1.5)
                        starting_month = 'januari 2020'
                        driver.execute_script("window.scrollTo(0,100);")
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
                        wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
                        driver.execute_script("window.scrollTo(0,850);")
                        time.sleep(2)
                        consumption_graph_container = driver.find_element_by_id('consumption-graph-container')
                        highcharts_subtitle = consumption_graph_container.find_element_by_class_name('highcharts-subtitle')
                        previous_link = consumption_graph_container.find_element_by_class_name('link-previous')
                        next_link = consumption_graph_container.find_element_by_class_name('link-next')
                        # try:
                        #     unit = highcharts_subtitle.find_element_by_tag_name('b').text.split()[-1]
                        # except NoSuchElementException:
                        #     next_link.click()
                        #     wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
                        download_button = consumption_graph_container.find_element_by_tag_name('button')
                        data_count = 0
                        while(data_count <= 3):
                            download_button.click()
                            time.sleep(2)
                            has_downloaded = False
                            download_sleep_count = 0
                            while(not has_downloaded and download_sleep_count < 30):
                                # print('Now waiting in download')
                                if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-4:] == 'xlsx' and download_sleep_count < 30 :
                                    has_downloaded = True
                                time.sleep(1)
                                download_sleep_count += 1
                                # print(download_sleep_count)
                            if download_sleep_count < 30:
                                complete_data_block = prepare_data(download_dir,facilityId,kind,unit,resolution,quantity)
                                log.data(complete_data_block)
                                log.info('Indexed data for facilityId {0}, count {1}, quantity {2}'.format(facilityId,data_count,quantity))
                            else:
                                print('Download failed')
                                log.info('Download failed for {0}, count {1}, quantity {2}'.format(facilityId,data_count,quantity))
                            # if(orientation%2 == 0):
                            #     if 'disabled' not in next_link.get_attribute('class'):
                            #         previous_link.click()
                            #     else:
                            #         break
                            # else:
                            if 'disabled' not in next_link.get_attribute('class'):
                                next_link.click()
                            else:
                                break
                            time.sleep(2)
                            wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
                            data_count += 1

                        orientation += 1
                        driver.execute_script("window.scrollTo(0,0);")
                        time.sleep(2)
                    
                #document.getElementsByTagName('consumption-heat-category-dropdown')[0].getElementsByClassName('consumption-filter-block-item')[0].getElementsByClassName('btn-dropdown')[0].getElementsByClassName('dropdown-menu')[0].getElementsByTagName('li')[1].getElementsByTagName('a')[0].click();
                #document.getElementsByTagName('consumption-heat-category-dropdown')[0].getElementsByClassName('consumption-filter-block-item')[0].getElementsByClassName('btn-dropdown')[0].getElementsByClassName('btn')[0].click()
            elif kind == 'El':
                #Selecting stuff is different here
                driver.execute_script("window.scrollTo(0,0);")
                time.sleep(2)
                resolution_btn_group = driver.find_elements_by_class_name('btn-group')[1]
                resolution_button = resolution_btn_group.find_elements_by_tag_name('button')[0]
                el_resolution = resolution_button.text
                resolution_button.click()
                time.sleep(2)
                wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
                from_date_select_el = driver.find_elements_by_class_name('input_container')[0]
                to_date_select_el = driver.find_elements_by_class_name('input_container')[1]
                driver.execute_script("document.getElementsByClassName('input_container')[0].getElementsByTagName('input')[0].readOnly = false;document.getElementsByClassName('input_container')[1].getElementsByTagName('input')[0].readOnly = false;")
                time.sleep(1)
                # from_date_select_el_input = from_date_select_el.find_element_by_tag_name('input')
                # from_date_select_el_input.clear()
                # from_date_select_el_input.send_keys("2019-01-01")
                # from_date_select_el_input.send_keys(Keys.RETURN)
                # time.sleep(1)
                # to_date_select_el_input = to_date_select_el.find_element_by_tag_name('input')
                # to_date_select_el_input.clear()
                # to_date_select_el_input.send_keys("2019-01-31")
                # to_date_select_el_input.send_keys(Keys.RETURN)
                # time.sleep(1)
                # wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
                # wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'compare-graph-data')))
                # unit_el = 'kWh'
                # consumption_date = driver.find_element_by_class_name("compare-graph-data")
                # if 'kWh' in consumption_date.text:
                #     unit_el = 'kWh'
                # if 'MWh' in consumption_date.text:
                #     unit_el = 'MWh'
                # driver.execute_script("window.scrollTo(0,850);")
                # time.sleep(2)
                # download_excel_el_button = driver.find_element_by_class_name('graph-container').find_element_by_class_name('btn')
                # next_button_el = driver.find_element_by_class_name('next_button')
                # wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
                # run_loop_download = True
                start_date = dt(2021,1,1)
                # end_date = dt(2019,1,31)
                while(1):
                    driver.execute_script("if(document.getElementsByClassName('_hj-widget-container')[0] != undefined){document.getElementsByClassName('_hj-widget-container')[0].style.display = 'none';}")
                    time.sleep(2)
                    end_date = start_date + relativedelta(days=30)
                    # print('setting date range {0} --:-- {1}'.format(dt.strftime(start_date,"%Y-%m-%d"),dt.strftime(end_date,"%Y-%m-%d")))
                    from_date_select_el = driver.find_elements_by_class_name('input_container')[0]
                    to_date_select_el = driver.find_elements_by_class_name('input_container')[1]

                    to_date_select_el_input = to_date_select_el.find_element_by_tag_name('input')
                    to_date_select_el_input.clear()

                    from_date_select_el_input = from_date_select_el.find_element_by_tag_name('input')
                    from_date_select_el_input.clear()
                    # time.sleep(1)
                    from_date_select_el_input.send_keys(dt.strftime(start_date,"%Y-%m-%d"))
                    # time.sleep(0.75)
                    from_date_select_el_input.send_keys(Keys.RETURN)
                    time.sleep(2)

                    from_date_select_el_input = from_date_select_el.find_element_by_tag_name('input')
                    from_date_select_el_input.clear()
                    # time.sleep(1)
                    from_date_select_el_input.send_keys(dt.strftime(start_date,"%Y-%m-%d"))
                    # time.sleep(0.75)
                    from_date_select_el_input.send_keys(Keys.RETURN)
                    time.sleep(2)
                    
                    to_date_select_el_input = to_date_select_el.find_element_by_tag_name('input')
                    to_date_select_el_input.clear()
                    # time.sleep(1)
                    to_date_select_el_input.send_keys(dt.strftime(end_date,"%Y-%m-%d"))
                    # time.sleep(0.75)
                    to_date_select_el_input.send_keys(Keys.RETURN)
                    time.sleep(2)

                    to_date_select_el_input = to_date_select_el.find_element_by_tag_name('input')
                    to_date_select_el_input.clear()
                    # time.sleep(1)
                    to_date_select_el_input.send_keys(dt.strftime(end_date,"%Y-%m-%d"))
                    # time.sleep(0.75)
                    to_date_select_el_input.send_keys(Keys.RETURN)
                    time.sleep(2)

                    # next_button_el = driver.find_element_by_class_name('next_button')
                    
                    # if 'btn_disable' in next_button_el.get_attribute('class'):
                    #     break
                    #     print('Here in break')
                    driver.execute_script("window.scrollTo(0,850);")
                    time.sleep(2)
                    wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
                    # download_excel_el_button = driver.find_element_by_class_name('graph-container').find_element_by_class_name('btn')
                    
                    # wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'next_button')))
                    # time.sleep(1)
                    # download_excel_el_button.click()
                    # time.sleep(2)
                    year_el_download_button = driver.find_element_by_class_name('mart20').find_element_by_class_name('btn')
                    year_el_download_button.click()
                    time.sleep(2)
                    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'spinner')))
                    has_downloaded = False
                    download_sleep_count = 0
                    while(not has_downloaded and download_sleep_count < 25):
                        # print('Now waiting in download')
                        if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-4:] == 'xlsx' and download_sleep_count < 25 :
                                has_downloaded = True
                        time.sleep(1)
                        download_sleep_count += 1
                        # print(download_sleep_count)
                    if download_sleep_count < 25:
                        complete_data_block = prepare_data_el(download_dir,facilityId,start_date.year)
                        # print(complete_data_block[:10])
                        log.data(complete_data_block)
                        log.info('Indexed data for facilityId {0}'.format(facilityId))
                    else:
                        print('Download failed')
                        log.info('Download failed for {0}'.format(facilityId))
                    # next_button_el = driver.find_element_by_class_name('next_button')
                    # next_button_el.click()
                    # time.sleep(2)
                    # wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))
                    driver.execute_script("window.scrollTo(0,250)")
                    time.sleep(2)
                    start_date = start_date - relativedelta(years=1)
                    if start_date.year == 2018:
                        # print('Here in break')
                        break
                    # end_date = end_date + relativedelta(days=31)
        
        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,"Successfully scraped data for all available facilities")

        

        #wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'loading-spinner')))

        # kind_lookup = {'heat-1.svg':'Fjärrvärme','heat-2.svg':'Fjärrvärme','Cool-1.svg':'Fjärrkyla','el-1.svg':'Elnät','el-2.svg':'Elnät'}
        # month_days = ['31','28','31','30','31','30','31','31','30','31','30','31']
        # months = {0:'Januari',1:'Februari',2:'Mars',3:'April',4:'Maj',5:'Juni',6:'Juli',7:'Augusti',8:'September',9:'Oktober',10:'November',11:'December'}





    
    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())
    
    driver.close()
    os.rmdir(download_dir)