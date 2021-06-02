from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException,TimeoutException
import time
import os
import traceback
import threading
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta


from common import get_driver
from common import Log
import config


def prepare_data(download_dir,selected_resolution):
    f = os.listdir(download_dir)[0]
    with open(os.path.join(download_dir,f),encoding='ISO-8859-1') as g:
        file_lines = g.readlines()
        typ = file_lines[0].split(';')[1].strip()
        facilityId = file_lines[1].split(';')[1].replace("'","").strip()
        complete_data_block = []
        for i in range(3,len(file_lines)):
            if ';' in file_lines[i]:
                data_block = {'facilityId':facilityId,'kind':typ,'unit':'kWh','quantity':'ENERGY'}
                start_date = file_lines[i].split(';')[0]
                data_block['startDate'] = start_date
                start_date_obj = dt.strptime(start_date, '%Y-%m-%d %H:%M:%S')
                if selected_resolution == 'Månad':
                    end_date_obj = start_date_obj + relativedelta(months=1)
                if selected_resolution == 'Timme':
                    end_date_obj = start_date_obj + relativedelta(hours=1)
                if selected_resolution == 'Dag':
                    end_date_obj = start_date_obj + relativedelta(days=1)
                if selected_resolution == 'År':
                    end_date_obj = start_date_obj + relativedelta(years=1)
                data_block['endDate'] = dt.strftime(end_date_obj, '%Y-%m-%d %H:%M:%S')
                data_block['value'] = file_lines[i].split(';')[1].strip()
                complete_data_block.append(data_block)
    os.remove(os.path.join(download_dir,f))
    print('Deleted the file')
    return complete_data_block


def UmeaEnergi(agentRunContext):

    log = Log(agentRunContext)

    try:

        log.job(config.JOB_RUNNING_STATUS,'UmeaEnergi thread started execution')

        # url = 'https://www.umeaenergi.se/mina-sidor/login'

        thread_id = str(threading.get_ident())
        download_dir = os.path.join(os.getcwd(),'temp','temp-'+thread_id)

        log.info('UmeaEnergi with threadID {0} has its temp directory in {1}'.format(thread_id,download_dir))

        driver = get_driver(download_dir)
        driver.maximize_window()
        driver.get(agentRunContext.homeURL)

        #Accept cookies 
        #-----------------------------------
        wait = WebDriverWait(driver,20)
        time.sleep(5)
        wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div/div[3]/div/div/div[2]/div/div/button')))
        driver.find_element_by_xpath('/html/body/div/div[3]/div/div/div[2]/div/div/button').click()

        log.info('Accepted Cookies')
        #-------------------------------------

        #Login
        #-------------------------------------
        driver.find_element_by_id('sectionplaceholder_1_rowplaceholderec931a9bef844079a92fd532f121cae1_0_blockplaceholder1013ddee3ff2e4f9383371ec262ea3ef1_0_Login1_UserName').send_keys(agentRunContext.requestBody['username'])
        driver.find_element_by_id('sectionplaceholder_1_rowplaceholderec931a9bef844079a92fd532f121cae1_0_blockplaceholder1013ddee3ff2e4f9383371ec262ea3ef1_0_Login1_Password').send_keys(agentRunContext.requestBody['password'])
        driver.find_element_by_id('sectionplaceholder_1_rowplaceholderec931a9bef844079a92fd532f121cae1_0_blockplaceholder1013ddee3ff2e4f9383371ec262ea3ef1_0_Login1_LoginButton').click()
        #--------------------------------------

        wait = WebDriverWait(driver,30)

        #Wait for login success
        #-------------------------------------
        try:
            #Wait until the next page [Detailed statistics button] is loaded for 30 secs
            wait.until(presence_of_element_located((By.XPATH,'//*[@id="statistics"]/div[2]/div[1]/div/div[2]/div[2]/a[1]')))
        except TimeoutException:
            #Login was not successfull, return proper response here
            #Better idea would be to dump it to elastic, message along with job_status COMPLETED_FAILED
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Not able to login, wrong username or password')
            driver.close()
            return
        #-------------------------------------
            
        log.job(config.JOB_RUNNING_STATUS,'Logged in')

        deta = driver.find_element_by_xpath('//*[@id="statistics"]/div[2]/div[1]/div/div[2]/div[2]/a[1]')

        if deta is None:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,"Page did not load properly,try again later")
            driver.close()
            # print('deta is none')
            return

        deta.click()

        #Wait for statistics wrapper
        wait.until(presence_of_element_located((By.XPATH,'/html/body/form/div[3]/div[2]/div[1]/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div/div[1]/div[1]')))

        time.sleep(5)

        #scroll down a bit
        driver.execute_script('window.scrollTo(0,window.scrollY+100);')

        time.sleep(5)

        #Remove all Lagg Till elements as they would interfere with click, because they are in the middle of the div
        #-------------------------------------
        js = 'for(var i=0;i<document.getElementsByClassName("arrow-right underline-text").length;i++){document.getElementsByClassName("arrow-right underline-text")[i].style.display = "none";}'
        driver.execute_script(js)
        #-------------------------------------

        wrapperScroll = 30

        count = 2
        
        log.job(config.JOB_RUNNING_STATUS,'Started scraping data')

        while(1):
            try:
                print(count)

                try:
                    #Implicit wait till the element we want to click is loaded on the page
                    wait.until(presence_of_element_located((By.XPATH,'/html/body/form/div[3]/div[2]/div[1]/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div/div[1]/div[1]/div['+str(count)+']')))
                except TimeoutException as e:
                    break

                #Find the current interested facility
                curr_facility = driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div[1]/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div/div[1]/div[1]/div['+str(count)+']')

                #Click on the facility
                curr_facility.click()

                time.sleep(2)

                #Details about the facility
                details = ';'.join([e.text for e in curr_facility.find_elements_by_class_name('ng-binding')])

                print('details {0}'.format(details))

                #Graph chart div
                chart = driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div[1]/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div/div[2]/div[3]/div[1]/div[2]')

                #Error div 
                error_block = driver.find_element_by_xpath('/html/body/form/div[3]/div[1]/div[4]')

                if 'none' not in error_block.get_attribute('style'):
                    error_block.find_elements_by_class_name("close-btn")[0].click()
                    time.sleep(2)
                    count += 1
                    print('skipped {0} because of errors'.format(details))
                    continue

                # /html/body/form/div[3]/div[1]/div[4]

                loader = driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div[1]/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div/div[2]/div[3]/div[1]/div[1]')

                #Sleep until chart is None and error is None
                while('ng-hide' not in loader.get_attribute("class")):
                    time.sleep(1)
                        
                time.sleep(5)

                print(error_block.get_attribute('style'))

                #Resolution select Select Webelement
                resolution_select = Select(driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div[1]/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div/div[2]/div[3]/div[2]/div[1]/div/div/div[1]/select'))

                #Available  resolution options for this facility
                resolution_options = resolution_select.options

                print('resolution options : {0}'.format(';'.join([e.text for e in resolution_options])))

                #Select the last option that is available, that is most detailed, further process this while reading the csv file
                selected_resolution = resolution_options[-1].text

                print(selected_resolution)

                #Select the resolution option
                resolution_select.select_by_visible_text(selected_resolution)

                # #Select webelement for period
                # period_select = Select(driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div[1]/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div/div[2]/div[3]/div[2]/div[1]/div/div/div[2]/div[2]/select'))

                # #Select the option for custom dates
                # period_select.select_by_visible_text('Valfritt datum')

                # time.sleep(1)

                # #Select from date to be 2018-01-01 for now we are able to download data for all facilities with this
                # picker_from = driver.find_element_by_id('pickerfrom')
                # picker_from.clear()
                # picker_from.send_keys('2018-01-01')

                #Find export_csv button and click on it
                #-------------------------------------
                export_csv = driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div[1]/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div/div[2]/div[3]/div[2]/div[3]/div/div/a[2]')
                export_csv.click()
                #-------------------------------------

                #Sleep indefineitly until the chart is loaded
                while('block' not in chart.get_attribute("style")):
                    print('In here waiting for char to come back')
                    time.sleep(1)
                
                print('Came out of chart wait')
                        
                #Wait for 15 secs for download in the temp directory
                #-------------------------------------
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
                    # print('Download failed')
                #-------------------------------------

                log.info('Successfully downloaded {0}'.format(details))
                # print('Successfully downloaded {0}'.format(details))

                #Scroll wrapper div a bit every iteration
                #-------------------------------------
                driver.execute_script('document.getElementsByClassName("statistics-delsite-wrapper")[0].scrollTo(0,'+str(wrapperScroll)+');')
                wrapperScroll += 30
                #-------------------------------------

                complete_data_block = prepare_data(download_dir,selected_resolution)

                log.data(complete_data_block)

                resolution_select.select_by_visible_text(resolution_options[0].text)

                driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div[1]/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div/div[2]/div[3]/div[2]/div[3]/div/div/a[1]').click()

                while('ng-hide' not in loader.get_attribute("class")):
                    time.sleep(1)

                print('selected month to avoid errors')

                count += 1
                    
            except Exception as e:
                log.exception(traceback.format_exc())
                log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
                driver.close()
                return
                
        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,'Successfully crawled the website for all the available facilities')
        os.rmdir(download_dir)
    
    except Exception as e:
        log.exception(traceback.format_exc())
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))

    driver.close()

