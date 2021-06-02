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

def prepare_data(facility_id,download_dir,selected_resolution,unit,utility_id,cols):
    cols.append('nan')
    complete_data_block = []
    f = os.listdir(download_dir)[0]
    with open(os.path.join(download_dir,f),'r',encoding='utf-8') as g:
        kind = g.readlines()[4].split()[1].strip()
    df = pd.read_csv(os.path.join(download_dir,f),sep='\t',skiprows=[0,1,2,3,4,5,6],names=cols,encoding='utf-8')
    for i in range(len(df)):
        if selected_resolution == 'Månad'.lower():
            start_date = parse(df['datetime'][i]+'-01')
            end_date = start_date + relativedelta(months=1)
        if selected_resolution == 'Timme'.lower():
            start_date = parse(df['datetime'][i])
            end_date = start_date + relativedelta(hours=1)
        if selected_resolution == 'Dag'.lower():
            start_date = parse(df['datetime'][i])
            end_date = start_date + relativedelta(days=1)
        if selected_resolution == 'År'.lower():
            start_date = parse(df['datetime'][i]+'-01-01')
            end_date = start_date + relativedelta(years=1)
        
        if utility_id == 'E' or utility_id == 'G' or utility_id == 'P':
            complete_data_block.append({'facilityId':facility_id,'startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['consumption'][i],'unit':unit,'quantity':'ENERGY','kind':kind})
        if utility_id == 'V':
            complete_data_block.append({'facilityId':facility_id,'startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['consumption'][i],'unit':unit,'quantity':'VOLUME','kind':kind})
        if utility_id == 'F' or utility_id == 'K':
            complete_data_block.append({'facilityId':facility_id,'startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['consumption'][i],'unit':unit,'quantity':'ENERGY','kind':kind})
            if 'flode' in cols and pd.notna(df['flode'][i]):
                complete_data_block.append({'facilityId':facility_id,'startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['flode'][i],'unit':'m3','quantity':'VOLUME','kind':kind})
            if 'dt' in cols and pd.notna(df['dt'][i]):
                complete_data_block.append({'facilityId':facility_id,'startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['dt'][i],'unit':'C','quantity':'TEMPERATURE','kind':kind})
            if 'graddagskorrigerad' in cols and pd.notna(df['graddagskorrigerad'][i]):
                complete_data_block.append({'facilityId':facility_id,'startDate':dt.strftime(start_date,'%Y-%m-%d %H:%M:%S'),'endDate':dt.strftime(end_date,'%Y-%m-%d %H:%M:%S'),'value':df['graddagskorrigerad'][i],'unit':unit,'quantity':'ENERGY_DDADJUSTED','kind':kind})
    
    os.remove(os.path.join(download_dir,f))

    return complete_data_block

def SimilarTemplateCrawlersReports(agentRunContext):

    log = Log(agentRunContext)

    try:

        start = time.time()

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
        
        log.info(str(important_ds))

        driver.execute_script('window.location.href = "{0}/Reports/Reports.aspx";'.format(base_path))

        time.sleep(1)

        try:
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME,'dvTriggerTree')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'No facility data available')
            driver.close()
            os.rmdir(download_dir)
            return

        end = time.time()

        print('Time taken to gather facility_ids is {0}'.format(end-start))

        log.job(config.JOB_RUNNING_STATUS,'Started scraping data')

        #Resolution for Heating and Vatten : Dag, El : Timme
        available_resolution = {'E':'Timme','V':'Dag','F':'Dag','G':'Timme','K':'Dag','P':'Dag'}

        wait = WebDriverWait(driver,100)

        #Click on them one by one and try to collect data

        index = -1
        prev_index = -1

        while(1):

            print('In loop here')

            time.sleep(2)

            try:
                driver.find_element_by_class_name('dvTriggerTree').click()
            except StaleElementReferenceException:
                log.info('Stale Element exception occured at {0}'.format(key))
                print(traceback.format_exc())
                log.exception(traceback.format_exc())
                log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
                driver.close()
                return

            time.sleep(1.5)

            while(len(driver.find_element_by_id('tree').get_attribute('class').split()) == 1):
                time.sleep(1)
            
            table_facilities = driver.find_element_by_id('tvCustomTreeView').find_elements_by_tag_name('table')

            for i in range(len(table_facilities)):
                if r'sC\\Z||' in table_facilities[i].find_element_by_tag_name('a').get_attribute('href') and i > index:
                    index = i
                    break
            
            curr_facility = table_facilities[index]

            print('final',curr_facility.find_element_by_tag_name('a').get_attribute('href'))

            if prev_index == index:
                break
            
            prev_index = index

            #Here have to check whether this is selected

            wait_needed = False

            key = curr_facility.find_element_by_tag_name('a').get_attribute('href').split('||')[1].replace(')','').replace("'",'')

            try:
                curr_facility.find_element_by_class_name('treeview-selected-node')
                time.sleep(1)
                driver.find_element_by_class_name('closeTree').click()
                time.sleep(1.5)
            except NoSuchElementException:
                wait_needed = True
                curr_facility.click()
                time.sleep(2)


            # if curr_facility.find_element_by_class_name('treeview-selected-node') == None:
            #     wait_needed = True
            #     curr_facility.click()
            # else:
            #     driver.find_element_by_class_name('closeTree').click()
            #     time.sleep(1.5)

            try:
                while(len(driver.find_element_by_id('tree').get_attribute('class').split()) == 2 and wait_needed):
                    time.sleep(1)
            except NoSuchElementException:
                print('{0} has no facilities so skipping'.format(key))
                log.info('{0} id does not have any facilities so skipping'.format(key))
                # driver.back()
                print('Tried to execute','window.location.href = "{0}/Reports/Reports.aspx";'.format(base_path))
                driver.execute_script('window.location.href = "{0}/Contract/Contracts.aspx";'.format(base_path))
                time.sleep(3)
                driver.execute_script('window.location.href = "{0}/Reports/Reports.aspx";'.format(base_path))
                wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'dvTriggerTree')))
                continue

            time.sleep(2)


            driver.execute_script("document.getElementById('dvUtilityTab').style.position = 'absolute';")

            utility_div = driver.find_element_by_id('dvUtilityTab')

            lis = utility_div.find_elements_by_tag_name('li')

            for j in range(1,len(lis)):
                k = lis[j]
                i = j-1
                while i>=0 and lis[i].find_element_by_tag_name('a').get_attribute("accessKey") > k.find_element_by_tag_name('a').get_attribute("accessKey"):
                    lis[i+1] = lis[i]
                    i = i-1
                lis[i+1] = k

            for li in lis:
                time.sleep(2)
                wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'ajax-loading')))

                utility_id = li.find_element_by_tag_name('a').get_attribute("accessKey")

                try:
                    facility_id = important_ds[key][utility_id]
                except KeyError as e:
                    log.info('{0} with utility {1} facility has no id, so choosing address'.format(key,utility_id))
                    facility_id = important_ds_addr[key]
                
                li.find_element_by_tag_name('a').click()

                wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'ajax-loading')))

                wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/form/div[3]/div/div/div[3]/div[3]/div[2]/div/div/div[3]/div[1]/section/article/div[1]/div[2]/select')))

                select_resolution = Select(driver.find_element_by_xpath('/html/body/form/div[3]/div/div/div[3]/div[3]/div[2]/div/div/div[3]/div[1]/section/article/div[1]/div[2]/select'))

                selected_resolution = available_resolution[utility_id].lower()

                if selected_resolution not in [u.text.lower() for u in select_resolution.options]:
                    select_resolution = Select(driver.find_element_by_xpath('/html/body/form/div[3]/div/div/div[3]/div[3]/div[2]/div/div/div[3]/div[1]/section/article/div[1]/div[2]/select'))
                    selected_resolution = select_resolution.options[-1].text
                    select_resolution.select_by_visible_text(selected_resolution)
                else:
                    for i,op in enumerate(select_resolution.options):
                        if selected_resolution == op.text.lower():
                            select_resolution = Select(driver.find_element_by_xpath('/html/body/form/div[3]/div/div/div[3]/div[3]/div[2]/div/div/div[3]/div[1]/section/article/div[1]/div[2]/select'))
                            select_resolution.select_by_visible_text(op.text)
                
                time.sleep(2)

                # time.sleep(2)
                unit = Select(driver.find_element_by_id('ddlUnit')).first_selected_option.text

                cols = ['datetime','consumption']
                try:
                    driver.execute_script("""for(var i=0;i<document.getElementsByClassName('chartOptionChk').length;i++){
                                                    if(document.getElementsByClassName('chartOptionChk')[i].getElementsByTagName('input')[0].getAttribute('disabled') == null && document.getElementsByClassName('chartOptionChk')[i].innerText == 'dT'){document.getElementsByClassName('chartOptionChk')[i].getElementsByTagName('input')[0].click();}}
                                                for(var i=0;i<document.getElementsByClassName('chartOptionChk').length;i++){ 
                                                    if(document.getElementsByClassName('chartOptionChk')[i].getElementsByTagName('input')[0].getAttribute('disabled') == null && document.getElementsByClassName('chartOptionChk')[i].innerText == 'Flöde'){document.getElementsByClassName('chartOptionChk')[i].getElementsByTagName('input')[0].click();}}
                                                for(var i=0;i<document.getElementsByClassName('chartOptionChk').length;i++){ 
                                                    if(document.getElementsByClassName('chartOptionChk')[i].getElementsByTagName('input')[0].getAttribute('disabled') == null && document.getElementsByClassName('chartOptionChk')[i].innerText == 'Graddagskorrigerad'){document.getElementsByClassName('chartOptionChk')[i].getElementsByTagName('input')[0].click();}}""")
                    # time.sleep(2)
                    dvLoad = driver.find_element_by_id('dvloadOption')

                    divs = dvLoad.find_elements_by_class_name('chartOptionChk')


                    for i in range(len(divs)-1,-1,-1):
                        if divs[i].text == 'Graddagskorrigerad':
                            cols.append('graddagskorrigerad')
                            continue
                        if divs[i].text == 'Flöde':
                            cols.append('flode')
                            continue
                        if divs[i].text == 'dT':
                            cols.append('dt')
                            continue
                        
                except JavascriptException:
                    print('Couldnt select more data for F')
                
                time.sleep(2)

                driver.execute_script("document.getElementById('optCSV').click();document.getElementById('btnExport').click();")

                time.sleep(2)

                has_downloaded = False
                download_sleep_count = 0
                while(not has_downloaded  and download_sleep_count < 25):
                    if(len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-3:] == 'csv' and download_sleep_count < 25):
                        has_downloaded = True
                    time.sleep(1)
                    download_sleep_count += 1
                    
                if download_sleep_count >= 25:
                    log.info('Download for facility_id {0} with useplaceid {1} failed'.format(facility_id,key))
                    continue
                    
                complete_data_block = prepare_data(facility_id,download_dir,selected_resolution.lower(),unit,utility_id,cols)

                log.data(complete_data_block)

                log.info('Indexed data for facility_id {0} with useplaceid {1}'.format(facility_id,key))

            # driver.find_element_by_class_name('dvTriggerTree').click()

        #----------------------------------------------------

#         for key in important_ds.keys():

#             if not ('E' in important_ds[key].keys() or 'V' in important_ds[key].keys() or 'G' in important_ds[key].keys() or 'F' in important_ds[key].keys() or 'K' in important_ds[key].keys()):
#                 continue

#             # if 'T' in important_ds[key].keys() and len(important_ds[key].keys()) == 1 :
#             #     continue

#             driver.execute_script(r"__doPostBack('ctl00$MainContent$tvCustomTreeView$tvCustomTreeView','sC\\Z||{0}')".format(key))

#             time.sleep(8)

#             print(r"__doPostBack('ctl00$MainContent$tvCustomTreeView$tvCustomTreeView','sC\\Z||{0}')".format(key))

#             wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'ajax-loading')))

#             time.sleep(2)
# # 
#             #Traverse the list here for all the facilities in this address

#             try:
#                 WebDriverWait(driver,10).until(presence_of_element_located((By.ID,'menuNavbar')))
#             except TimeoutException as e:
#                 print('{0} id does not have any facilities so skipping'.format(key))
#                 log.info('{0} id does not have any facilities so skipping'.format(key))
#                 # driver.back()
#                 print('Tried to execute','window.location.href = "{0}/Reports/Reports.aspx";'.format(base_path))
#                 driver.execute_script('window.location.href = "{0}/Contract/Contracts.aspx";'.format(base_path))
#                 time.sleep(2)
#                 driver.execute_script('window.location.href = "{0}/Reports/Reports.aspx";'.format(base_path))
#                 wait.until(presence_of_element_located((By.ID,'dvReportChart')))
#                 continue

#             driver.execute_script("document.getElementById('dvUtilityTab').style.position = 'absolute';")

#             utility_div = driver.find_element_by_id('dvUtilityTab')

#             lis = utility_div.find_elements_by_tag_name('li')

#             while(len(lis) != len(important_ds[key].keys())):
#                 time.sleep(1)

#             for j in range(1,len(lis)):
#                 k = lis[j]
#                 i = j-1
#                 while i>=0 and lis[i].find_element_by_tag_name('a').get_attribute("accessKey") > k.find_element_by_tag_name('a').get_attribute("accessKey"):
#                     lis[i+1] = lis[i]
#                     i = i-1
#                 lis[i+1] = k

#             for li in lis:
#                 time.sleep(2)
#                 wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'ajax-loading')))
#                 # try:
#                 #     click_a = li.find_element_by_tag_name('a')
#                 # except StaleElementReferenceException as e:
#                 #     print('In error',len(lis))
#                 #     break


#                 utility_id = li.find_element_by_tag_name('a').get_attribute("accessKey")

#                 try:
#                     facility_id = important_ds[key][utility_id]
#                 except KeyError as e:
#                     log.info('{0} with utility {1} facility has no id, so choosing address'.format(key,utility_id))
#                     facility_id = important_ds_addr[key]

#                 li.find_element_by_tag_name('a').click()

#                 wait.until(EC.invisibility_of_element_located((By.CLASS_NAME,'ajax-loading')))

#                 wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/form/div[3]/div/div/div[3]/div[3]/div[2]/div/div/div[3]/div[1]/section/article/div[1]/div[2]/select')))

#                 select_resolution = Select(driver.find_element_by_xpath('/html/body/form/div[3]/div/div/div[3]/div[3]/div[2]/div/div/div[3]/div[1]/section/article/div[1]/div[2]/select'))

#                 selected_resolution = available_resolution[utility_id].lower()

#                 if selected_resolution not in [u.text.lower() for u in select_resolution.options]:
#                     select_resolution = Select(driver.find_element_by_xpath('/html/body/form/div[3]/div/div/div[3]/div[3]/div[2]/div/div/div[3]/div[1]/section/article/div[1]/div[2]/select'))
#                     selected_resolution = select_resolution.options[-1].text
#                     select_resolution.select_by_visible_text(selected_resolution)
#                 else:
#                     for i,op in enumerate(select_resolution.options):
#                         if selected_resolution == op.text.lower():
#                             select_resolution = Select(driver.find_element_by_xpath('/html/body/form/div[3]/div/div/div[3]/div[3]/div[2]/div/div/div[3]/div[1]/section/article/div[1]/div[2]/select'))
#                             select_resolution.select_by_visible_text(op.text)
                
#                 time.sleep(2)

#                 # time.sleep(2)
#                 unit = Select(driver.find_element_by_id('ddlUnit')).first_selected_option.text

#                 cols = ['datetime','consumption']
#                 try:
#                     driver.execute_script("""for(var i=0;i<document.getElementsByClassName('chartOptionChk').length;i++){
#                                                     if(document.getElementsByClassName('chartOptionChk')[i].getElementsByTagName('input')[0].getAttribute('disabled') == null && document.getElementsByClassName('chartOptionChk')[i].innerText == 'dT'){document.getElementsByClassName('chartOptionChk')[i].getElementsByTagName('input')[0].click();}}
#                                                 for(var i=0;i<document.getElementsByClassName('chartOptionChk').length;i++){ 
#                                                     if(document.getElementsByClassName('chartOptionChk')[i].getElementsByTagName('input')[0].getAttribute('disabled') == null && document.getElementsByClassName('chartOptionChk')[i].innerText == 'Flöde'){document.getElementsByClassName('chartOptionChk')[i].getElementsByTagName('input')[0].click();}}
#                                                 for(var i=0;i<document.getElementsByClassName('chartOptionChk').length;i++){ 
#                                                     if(document.getElementsByClassName('chartOptionChk')[i].getElementsByTagName('input')[0].getAttribute('disabled') == null && document.getElementsByClassName('chartOptionChk')[i].innerText == 'Graddagskorrigerad'){document.getElementsByClassName('chartOptionChk')[i].getElementsByTagName('input')[0].click();}}""")
#                     # time.sleep(2)
#                     dvLoad = driver.find_element_by_id('dvloadOption')

#                     divs = dvLoad.find_elements_by_class_name('chartOptionChk')


#                     for i in range(len(divs)-1,-1,-1):
#                         if divs[i].text == 'Graddagskorrigerad':
#                             cols.append('graddagskorrigerad')
#                             continue
#                         if divs[i].text == 'Flöde':
#                             cols.append('flode')
#                             continue
#                         if divs[i].text == 'dT':
#                             cols.append('dt')
#                             continue
                        
#                 except JavascriptException:
#                     print('Couldnt select more data for F')
                
#                 time.sleep(2)

#                 driver.execute_script("document.getElementById('optCSV').click();document.getElementById('btnExport').click();")

#                 time.sleep(2)

#                 has_downloaded = False
#                 download_sleep_count = 0
#                 while(not has_downloaded):
#                     if(len(os.listdir(download_dir)) > 0 and os.listdir(download_dir)[0][-3:] == 'csv' and download_sleep_count < 25):
#                         has_downloaded = True
#                     time.sleep(1)
#                     download_sleep_count += 1
                    
#                 if download_sleep_count > 25:
#                     log.info('Download for facility_id {0} with useplaceid {1} failed'.format(facility_id,key))
#                     continue
                    
#                 complete_data_block = prepare_data(facility_id,download_dir,selected_resolution.lower(),unit,utility_id,cols)

#                 log.data(complete_data_block)

#                 log.info('Indexed data for facility_id {0} with useplaceid {1}'.format(facility_id,key))
        
        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,'Successfully scraped data for all the available facilities')

        os.rmdir(download_dir)
                        
    except Exception as e:
        print(traceback.format_exc())
        log.exception(traceback.format_exc())
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
    
    driver.close()
    