from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException,TimeoutException
import pandas as pd
import time
import os
import traceback
import threading


from common import get_driver
from common import Log
import config
from utilities import DayMonthYear

def SolorBioenergi(agentRunContext):
    
    log = Log(agentRunContext)

    #check for keys
    if agentRunContext.requestBody.get('city') is None:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,'city is a mandatory parameter')
        return
    
    if agentRunContext.requestBody.get('customerNumber') is None:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,'customerNumber is a mandatory parameter')
        return
    
    if agentRunContext.requestBody.get('orgNumber') is None:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,'orgNumber is a mandatory parameter')
        return

    log.job(config.JOB_RUNNING_STATUS,'Solor Bioenergi thread started execution')

    try:

        #Get a driver object
        # url = "https://www.kwhgreen.com/Login"
        thread_id = str(threading.get_ident())
        download_dir = os.path.join(os.getcwd(),'temp','temp-'+thread_id)

        log.info('SolorBioenergi with threadID {0} has its temp directory in {1}'.format(thread_id,download_dir))

        driver = get_driver(download_dir)
        driver.maximize_window()
        driver.get(agentRunContext.homeURL)

        wait = WebDriverWait(driver, 30)

        # to click on the Användarnamn username
        driver.find_element_by_id('MainContent_Email').send_keys(agentRunContext.requestBody['username'])

        # to click on the Lösenord password
        driver.find_element_by_id('MainContent_Password').send_keys(agentRunContext.requestBody['password'])

        # to click on the loggi button
        wait.until(presence_of_element_located((By.XPATH, '/html/body/form/div[4]/div[2]/div[1]/section/div/div[4]/div/input')))
        driver.find_element_by_xpath('/html/body/form/div[4]/div[2]/div[1]/section/div/div[4]/div/input').click()

        # to select the city
        try:
            wait.until(presence_of_element_located((By.XPATH, '/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[1]/tbody/tr/td[2]/select')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Unable to login, wrong username or password')
            driver.close()
            return
        city = Select(driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[1]/tbody/tr/td[2]/select'))
        city.select_by_visible_text(agentRunContext.requestBody['city'])

        time.sleep(2)

        wait.until(presence_of_element_located((By.XPATH, '/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[1]/tbody/tr/td[2]/select')))
        city = Select(driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[1]/tbody/tr/td[2]/select'))
        city.select_by_visible_text(agentRunContext.requestBody['city'])

        time.sleep(5)

        # to click on the Kundnummer(number)
        driver.find_element_by_id('ContentPlaceHolder1_tbxKundnummer').send_keys(agentRunContext.requestBody['customerNumber'])

        print('Gave customer number')

        time.sleep(5)

        # to click on the Person-/Org.-nummer YYMMDDABCD(number)
        driver.find_element_by_id('ContentPlaceHolder1_tbxIdNummer').send_keys(agentRunContext.requestBody['orgNumber'])

        # to click on the Hamta data(Show data) button
        wait.until(presence_of_element_located((By.XPATH, '/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[1]/tbody/tr/td[7]/input')))
        driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[1]/tbody/tr/td[7]/input').click()

        #Wait until the select element to select facilities is visible
        try:
            wait.until(presence_of_element_located((By.XPATH,'/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[2]/tbody/tr[4]/td[2]/select')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Wrong city or customerNumber or orgNumber')
            driver.close()
            return

        select = Select(driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[2]/tbody/tr[4]/td[2]/select'))

        for option in select.options:

            log.job(config.JOB_RUNNING_STATUS,'Started scraping data')

            facilityId = option.text.split('-')[0].strip()

            select.select_by_visible_text(option.text)

            log.info('selected and started scraping {0}'.format(facilityId))

            #Wait until the table is present
            wait.until(presence_of_element_located((By.XPATH,'/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[2]/tbody/tr[12]/td/div/table/tbody')))

            #Get tbody of the data table
            tbody = driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div/div[1]/div[1]/div/div/div/div[2]/div/div/table[2]/tbody/tr[12]/td/div/table/tbody')

            #for all the rows in the table
            trs = tbody.find_elements_by_tag_name("tr")

            header = []

            #Create header list
            for td in trs[0].find_elements_by_tag_name("th"):
                header.append(td.text)
            
            #list to hold list of row values
            complete_data = []

            #first row is the header row, so removing that for traversing
            trs = trs[1:]

            for tr in trs:
                curr = []
                for td in tr.find_elements_by_tag_name("td"):
                    curr.append(td.text)
                complete_data.append(curr)
            
            df = pd.DataFrame(complete_data,columns=header)

            months = ['Januari','Februari','Mars','April','Maj','Juni','Juli','Augusti','September','Oktober','November','December']

            complete_data_block = []

            startDate = '01'

            for i in range(len(df)):
                year = df['År'][i]
                for m in range(12):
                    data_block = {'facilityId':facilityId,'kind':'Fjärrvärme','quantity':'ENERGY','unit':'MWh'}
                    data_block['startDate'] = year+'-'+"{:02d}".format(m+1)+'-'+startDate
                    data_block['endDate'] = year+'-'+"{:02d}".format(m+1)+'-'+str(DayMonthYear(m+1,year))
                    data_block['value'] = df[months[m]][i]
                    complete_data_block.append(data_block)

            log.data(complete_data_block)
        
        log.job(config.JOB_COMPLETED_SUCCESS_STATUS,'Successfully crawled the website for all the available facilities')

        os.rmdir(download_dir)
    
    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.info(traceback.format_exc())
    
    driver.close()