import traceback
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException,TimeoutException,ElementNotInteractableException
import time
import os
import traceback
import threading
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from datetime import timedelta
import calendar
import pandas as pd


import config
from common import Log,get_driver

meridian_list = ['pm','am']

def find_meridian(meridian,ext_time):
    if '12:00:00' in ext_time:
        meridian += 1
    return meridian,ext_time+" "+meridian_list[meridian%2]

def prepare_data_el(download_dir):
    for f in os.listdir(download_dir):
        complete_data_block = []
        meridian = 0
        df = pd.read_csv(os.path.join(download_dir,f),nrows=1)
        facilityId = df['Installation'][0].split()[1]
        df = pd.read_csv(os.path.join(download_dir,f),skiprows=[0,1])
        for i in range(len(df)):
            data_block = {'facilityId':facilityId,'quantity':'ENERGY','kind':'EL'}
            meridian,d = find_meridian(meridian,df['DATETIME'][i])
            start_date = dt.strptime(d, "%Y-%m-%d %I:%M:%S %p")
            end_date = start_date + relativedelta(hours=1)
            data_block['startDate'] = dt.strftime(start_date,"%Y-%m-%d %H:%M:%S")
            data_block['endDate'] = dt.strftime(end_date,"%Y-%m-%d %H:%M:%S")
            data_block['value'] = df['VALUE'][i]
            data_block['unit'] = df['UNIT'][i]
            complete_data_block.append(data_block)
        os.remove(os.path.join(download_dir,f))
        return complete_data_block,facilityId

def hour_rounder(t):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return (t.replace(second=0, microsecond=0, minute=0, hour=t.hour)+timedelta(hours=t.minute//30))

def prepare_data_el_day(download_dir):
    for f in os.listdir(download_dir):
        complete_data_block = []
        facilityId = None
        with open(os.path.join(download_dir,f),'r') as g:
            facilityId = g.readlines()[2].split()[1]
        df = pd.read_csv(os.path.join(download_dir,f),skiprows=[0,1,2])
        for i in range(len(df)):
            if pd.notna(df['CONSUMPTUION'][i]):
                end_date = parse(df['READINGDATE'][i])
                start_date = end_date - relativedelta(hours=23,minutes=59)
                complete_data_block.append({'facilityId':facilityId,'kind':'El','quantity':'ENERGY','unit':'kWh','startDate':dt.strftime(start_date,"%Y-%m-%d %H:%M:%S"),'endDate':dt.strftime(end_date,"%Y-%m-%d %H:%M:%S"),'value':df['CONSUMPTUION'][i]})
        os.remove(os.path.join(download_dir,f))
        return complete_data_block,facilityId


def prepare_data_heating(download_dir):
    for f in os.listdir(download_dir):
        complete_data_block = []
        with open(os.path.join(download_dir,f),'r',encoding='utf-8') as g:
            file_lines = g.readlines()
            facilityId = file_lines[3].split(":")[1].replace('"','').strip()
        df = pd.read_csv(os.path.join(download_dir,f),skiprows=[0,1])
        for i in range(len(df)):
            start_date = dt.strptime(df['readingdate'][i],"%Y-%m-%d %H:%M:%S")
            end_date = start_date + relativedelta(days=1)

            complete_data_block.append({'facilityId':facilityId,'kind':'Fjärrvärme','startDate':dt.strftime(start_date,"%Y-%m-%d %H:%M:%S"),'endDate':dt.strftime(end_date,"%Y-%m-%d %H:%M:%S"),'value':df['kWhConsumption'][i],'unit':'kWh','quantity':'ENERGY'})

            complete_data_block.append({'facilityId':facilityId,'kind':'Fjärrvärme','startDate':dt.strftime(start_date,"%Y-%m-%d %H:%M:%S"),'endDate':dt.strftime(end_date,"%Y-%m-%d %H:%M:%S"),'value':df['M3Consumption'][i],'unit':'m3','quantity':'VOLUME'})
            
            complete_data_block.append({'facilityId':facilityId,'kind':'Fjärrvärme','startDate':dt.strftime(start_date,"%Y-%m-%d %H:%M:%S"),'endDate':dt.strftime(end_date,"%Y-%m-%d %H:%M:%S"),'value':df['AVERAGE_DELTAT'][i], 'unit':'C','quantity':'TEMPERATURE'})

        os.remove(os.path.join(download_dir,f))
        return complete_data_block,facilityId


def select_from_date(wait,driver,log):
    months = {'January':'Januari','February':'Februari','March':'Mars','April':'April','May':'Maj','June':'Juni','July':'Juli','August':'Augusti','September':'September','October':'Oktober','November':'November','December':'December'}
    #Caluclate the date to be set
    from_date = dt.now() - relativedelta(months=11)
    from_date_string = dt.strftime(from_date, "%Y-%m-%d").split('-')
    year = from_date_string[0]
    # month = calendar.month_name[int(from_date_string[1])]
    month = months[dt.strftime(from_date,'%B')][:3].upper()
    # month = 'JAN'
    date = from_date_string[2].lstrip('0')

    try:
        #Click on the year div, to select year
        wait.until(presence_of_element_located((By.XPATH,'/html/body/div[1]/div[2]/div/mat-datepicker-content/mat-calendar/mat-calendar-header/div/div/button[1]')))
        driver.find_element_by_xpath('/html/body/div[1]/div[2]/div/mat-datepicker-content/mat-calendar/mat-calendar-header/div/div/button[1]').click()

        time.sleep(2)

        year_tbody = driver.find_element_by_xpath('/html/body/div[1]/div[2]/div/mat-datepicker-content/mat-calendar/div/mat-multi-year-view/table/tbody')
        tds = year_tbody.find_elements_by_tag_name('td')
        for td in tds:
            if td.text == year:
                td.click()
                break
        #Once year is selected, it opens up the month tbody, from where the month is to be selected

        time.sleep(2)

        month_tbody = driver.find_element_by_xpath('/html/body/div[1]/div[2]/div/mat-datepicker-content/mat-calendar/div/mat-year-view/table/tbody')
        tds = month_tbody.find_elements_by_tag_name('td')
        for td in tds:
            if td.text == month:
                td.click()
                break
        
        #Once month is selected, it opens up date tbody, where date is to be selected

        time.sleep(2)

        date_tbody = driver.find_element_by_xpath('/html/body/div[1]/div[2]/div/mat-datepicker-content/mat-calendar/div/mat-month-view/table/tbody')
        tds = date_tbody.find_elements_by_tag_name('td')
        for td in tds:
            if td.text == date:
                td.click()
                break

        time.sleep(2)

    except Exception as e:
        log.exception(traceback.format_exc())
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))


def check_download(download_dir):
    #Wait until the file is downloaded for 25 secs
    has_downloaded = False
    download_sleep_count = 0
    while(not has_downloaded  and download_sleep_count < 30):
        if len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-3:] == 'csv' and download_sleep_count < 30 :
            has_downloaded = True
        time.sleep(1)
        download_sleep_count += 1
    
    return download_sleep_count



def SkellefteaKraft(agentRunContext):
    
    log = Log(agentRunContext)

    sections_downloaded = 0
    
    try:
        
        log.job(config.JOB_RUNNING_STATUS,'SkellfteaKraft thread started execution')

        thread_id = str(threading.get_ident())
        download_dir = os.path.join(os.getcwd(),'temp','temp-'+thread_id)

        log.info('SkellfteaKraft with threadID {0} has its temp directory in {1}'.format(thread_id,download_dir))

        driver = get_driver(download_dir)
        driver.maximize_window()
        driver.get(agentRunContext.homeURL)

        wait = WebDriverWait(driver,120)

        #Send in the keys for log in
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'form-check')))
        time.sleep(2)
        try:
            driver.find_element_by_xpath('/html/body/app-root/main/mp-lightbox[3]/div/div[2]/div/button').click()
            time.sleep(2)
        except ElementNotInteractableException:
            log.info('Removed cookies selection')
        driver.find_elements_by_class_name('form-check')[2].click()
        time.sleep(2)
        driver.find_elements_by_class_name('form-control')[0].send_keys(agentRunContext.requestBody['username'])
        time.sleep(2)
        driver.find_elements_by_class_name('form-control')[1].send_keys(agentRunContext.requestBody['password'])
        time.sleep(2)
        driver.find_elements_by_class_name('btn')[0].click()

        try:
            wait1 = WebDriverWait(driver,15)
            # wait1.until(EC.invisibility_of_element_located((By.TAG_NAME,'mp-loader')))
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'menu-main')))
            # wait1.until(EC.visibility_of_element_located((By.CLASS_NAME,'menu-main')))
        except TimeoutException as e:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to login, incorrect username or password')
            os.rmdir(download_dir)
            driver.close()
            return
        
        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')

        # #to open rapport
        # try:
        #     wait.until(presence_of_element_located((By.XPATH, '/html/body/app-root/div/mp-menu/header/div/div/div/nav/ul/li[4]/a')))
        # except TimeoutException as e:
        #     log.job(config.JOB_COMPLETED_FAILED_STATUS,'Not able to open reports tab')
        #     log.exception(traceback.format_exc())
        #     driver.close()
        #     return
        # driver.find_element_by_xpath('/html/body/app-root/div/mp-menu/header/div/div/div/nav/ul/li[4]/a').click()

        # time.sleep(2)

        wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'mp-loader')))

        driver.execute_script("window.location.href = '/reports'")

        time.sleep(2)

        wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'mp-loader')))

        time.sleep(2)

        report_groups = driver.find_elements_by_class_name("report-group")

        for report_group in report_groups:
            report_type = report_group.find_element_by_class_name("report-label")

            print(report_type.text)

            if report_type.text == "El" or report_type.text == "Fjärrvärme":

                # report_type.click()

                driver.execute_script('arguments[0].click();',report_type)

                time.sleep(2)

                driver.execute_script('window.scrollTo(0,300);')

                time.sleep(2)

                radio_buttons = driver.find_elements_by_class_name('form-check')

                for radio_button in radio_buttons:
                    print(radio_button.text)
                    if radio_button.text == 'Export av timvärden' or radio_button.text == 'Elnät dygnsförbrukning' or radio_button.text == 'Fjärrvärme dygnsförbrukning':

                        input_radio = radio_button.find_element_by_tag_name('input')

                        # input_radio.click()
                        driver.execute_script('arguments[0].click();',input_radio)

                        time.sleep(2)

                        driver.execute_script('window.scrollTo(0,600);')

                        time.sleep(2)

                        #Select facility

                        facility_select = Select(driver.find_elements_by_class_name('custom-select')[0])

                        facility_options = facility_select.options

                        print(facility_options)

                        for i in range(len(facility_options)):

                            print(facility_options[i].text)

                            facility_select.select_by_index(i)

                            time.sleep(2)

                            start_date_input = driver.find_elements_by_tag_name('mp-datepicker')[0].find_element_by_tag_name('input')

                            # start_date_input.click()

                            driver.execute_script('arguments[0].click();',start_date_input)

                            time.sleep(1)

                            select_from_date(wait,driver,log)

                            time.sleep(2)

                            end_date_input = driver.find_elements_by_tag_name('mp-datepicker')[1].find_element_by_tag_name('input')

                            driver.execute_script('arguments[0].click();',end_date_input)

                            time.sleep(1)

                            todays_date = driver.find_element_by_class_name('mat-calendar-body-today')

                            driver.execute_script('arguments[0].click();',todays_date)

                            time.sleep(1)

                            file_select = Select(driver.find_elements_by_class_name('custom-select')[1])

                            file_select.select_by_value('CSV')

                            time.sleep(1)

                            download_button = driver.find_element_by_class_name('btn')

                            driver.execute_script('arguments[0].click()',download_button)
                            time.sleep(1)

                            download_sleep_count = check_download(download_dir)

                            if download_sleep_count >= 30:
                                log.info('Download failed')
                                continue
                            
                            if radio_button.text == 'Elnät dygnsförbrukning':
                                complete_data_block,facilityId = prepare_data_el_day(download_dir)
                            elif radio_button.text == 'Export av timvärden' :
                                complete_data_block,facilityId = prepare_data_el(download_dir)
                            elif radio_button.text == 'Fjärrvärme dygnsförbrukning':
                                complete_data_block,facilityId = prepare_data_heating(download_dir)
                            
                            log.data(complete_data_block)

                            log.info('Indexed data with facilityId {0}'.format(facilityId))
                            print('Indexed data with facilityId {0}'.format(facilityId))

                driver.execute_script('arguments[0].click();',report_type)
            
            # if report_type.text == "Fjärrvärme":

            #     driver.execute_script('arguments[0].click();',report_type)

            #     time.sleep(2)

            #     driver.execute_script('window.scrollTo(0,300);')

            #     time.sleep(2)

            #     radio_buttons = driver.find_elements_by_class_name('form-check')

        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,"Successfully scraped data for all available facilities")




        # to open the EL
        # try:
        #     wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[1]/label')))
        #     driver.find_element_by_xpath('/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[1]/label').click()

        #     time.sleep(2)

        #     driver.execute_script('window.scrollTo(0,300);')

        #     time.sleep(2)


        #     #Click on export hourly values
        #     wait.until(presence_of_element_located((By.XPATH,'/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[1]/div/div[10]')))
        #     driver.find_element_by_xpath('/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[1]/div/div[10]').click()

        #     time.sleep(2)

        #     driver.execute_script('window.scrollTo(0,600);')

        #     time.sleep(2)

        #     #Trying to set `from` date, which would be today - 12 months

        #     #Clicked on the input tag to enter the value, which must be entered via clicking
        #     wait.until(presence_of_element_located((By.XPATH,'/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[1]/div/div[11]/div[3]/mp-datepicker/input')))
        #     driver.find_element_by_xpath('/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[1]/div/div[11]/div[3]/mp-datepicker/input').click()

        #     time.sleep(2)

        #     select_from_date(wait,driver,log)

        #     #Trying to set `to` date, which would be today's date

        #     wait.until(presence_of_element_located((By.XPATH,'/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[1]/div/div[11]/div[4]/mp-datepicker/input')))
        #     driver.find_element_by_xpath('/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[1]/div/div[11]/div[4]/mp-datepicker/input').click()

        #     time.sleep(2)
            
        #     #Click on today's date
        #     wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'mat-calendar-body-today')))
        #     driver.find_element_by_class_name('mat-calendar-body-today').click()

        #     time.sleep(2)

        #     #Select the file type to download
        #     wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[1]/div/div[11]/div[5]/select')))
        #     file_select = Select(driver.find_element_by_xpath('/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[1]/div/div[11]/div[5]/select'))

        #     time.sleep(2)

        #     file_select.select_by_value('CSV')

        #     time.sleep(2)

        #     #Click on the download button
        #     wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[1]/div/div[11]/div[6]')))
        #     driver.find_element_by_xpath('/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[1]/div/div[11]/div[6]').click()

        #     time.sleep(2)

        #     download_sleep_count = check_download(download_dir)
            
        #     if download_sleep_count >= 25:
        #         log.info('Failed to download csv for EL')
                
        #     else:
        #         log.info('Successfully downloaded csv for EL')
        #         log.job(config.JOB_RUNNING_STATUS,'Successfully downloaded csv for EL')
            
        #     complete_data_block = prepare_data_el(download_dir)
        #     log.data(complete_data_block)

        #     log.info('Indexed EL data to elastic')

        #     # log.job(config.JOB_COMPLETED_SUCCESS_STATUS,'Successfully indexed EL data to elastic')
        #     sections_downloaded += 1
        
        # except TimeoutException as e:
        #     log.job(config.JOB_RUNNING_STATUS,'EL section is not available,trying to download Fjärrvärme')

        #From here on out work on downloading Fjärrvärme values

        # time.sleep(2)

        # #Scroll down to be able to click on heating
        # driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')

        # time.sleep(2)

        # #Click on heating drop down
        # try:
        #     wait.until(presence_of_element_located((By.XPATH,'/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[3]/label')))
        #     driver.find_element_by_xpath('/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[3]/label').click()

        #     time.sleep(2)

        #     driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')

        #     time.sleep(2)

        #     #Click on daily values export radio button
        #     wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[3]/div/div[1]/label')))
        #     driver.find_element_by_xpath('/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[3]/div/div[1]/label').click()

        #     time.sleep(2)

        #     driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')

        #     time.sleep(2)

        #     #Trying to set `to` date, which would be today's date

        #     wait.until(presence_of_element_located((By.XPATH,'/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[3]/div/div[2]/div[2]/mp-datepicker/input')))
        #     driver.find_element_by_xpath('/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[3]/div/div[2]/div[2]/mp-datepicker/input').click()

            
        #     time.sleep(2)

        #     select_from_date(wait,driver,log)

        #     wait.until(presence_of_element_located((By.XPATH,'/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[3]/div/div[2]/div[3]/mp-datepicker/input')))
        #     driver.find_element_by_xpath('/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[3]/div/div[2]/div[3]/mp-datepicker/input').click()

        #     time.sleep(2)
            
        #     #Click on today's date
        #     wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'mat-calendar-body-today')))
        #     driver.find_element_by_class_name('mat-calendar-body-today').click()

        #     time.sleep(2)

        #     #Select the file type to download
        #     wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[3]/div/div[2]/div[4]/select')))
        #     file_select = Select(driver.find_element_by_xpath('/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[3]/div/div[2]/div[4]/select'))

        #     file_select.select_by_value('CSV')

        #     time.sleep(2)

        #     wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[3]/div/div[2]/div[5]')))
        #     driver.find_element_by_xpath('/html/body/app-root/main/section/div/mp-reports-page/div[2]/div[1]/mp-reports/div/div/div[3]/div/div[2]/div[5]').click()

        #     time.sleep(2)

        #     download_sleep_count = check_download(download_dir)

        #     if download_sleep_count >= 25:
        #         log.info('Failed to download csv for Fjärrvärme')
        #     else:
        #         log.info('Successfully downloaded csv for Fjärrvärme')
        #         log.job(config.JOB_RUNNING_STATUS,'Successfully downloaded csv for Fjärrvärme')
            
        #     complete_data_block = prepare_data_heating(download_dir)
        #     log.data(complete_data_block)

        #     log.info('Indexed Fjärrvärme data to elastic')

        #     # log.job(config.JOB_COMPLETED_SUCCESS_STATUS,'Successfully indexed Fjärrvärme data to elastic')

        #     sections_downloaded += 1
        
        # except TimeoutException as e:
        #     log.job(config.JOB_RUNNING_STATUS,'Failed to load Fjärrvärme section')
        #     log.info('Failed to load Fjärrvärme section')
        

        # if sections_downloaded == 0:
        #     log.job(config.JOB_COMPLETED_FAILED_STATUS,'Could not load any sections')
        
        # else:
        #     log.job(config.JOB_COMPLETED_SUCCESS_STATUS,'Successfully downloaded data')
        
        # 

    
    except Exception as e:
        # print(traceback.format_exc())
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
    
    driver.close()
    os.rmdir(download_dir)