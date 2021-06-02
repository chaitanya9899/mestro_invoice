from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException, JavascriptException, \
    StaleElementReferenceException
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


def SollentunaEnergiOchMiljo(agentRunContext):
    log = Log(agentRunContext)

    try:
        log.job(config.JOB_RUNNING_STATUS,'{0} thread started execution'.format(agentRunContext.requestBody['agentId']))
        thread_id = str(threading.get_ident())
        download_dir = os.path.join(os.getcwd(), 'temp', 'temp-' + thread_id)
        print(download_dir)
        log.info('{0} with threadID {1} has its temp directory in {2}'.format(agentRunContext.requestBody['agentId'],thread_id, download_dir))
        driver = get_driver(download_dir)
        driver.maximize_window()
        driver.get(agentRunContext.homeURL)
        wait = WebDriverWait(driver, 100)

        # agentRunContext.requestBody['username']
        # agentRunContext.requestBody['password']
        # Login The With credential



		#driver.find_element_by_xpath('/html/body/form/div[4]/div/div[2]/div[3]/div/div[1]/div[2]/div/ul/li[2]').click()
		#driver.execute_script(('window.scrollTo(0,100);'))
		startlink=1

		    
		time.sleep(5)
		driver.find_element_by_xpath("/html/body/div/div/a").click()
		time.sleep(5)
		driver.find_element_by_xpath("/html/body/form/div[3]/main/div[2]/div[1]/div/div/div[1]/ul/li[2]").click()
		time.sleep(5)
		# to click on the Användarnamn usern

		driver.find_element_by_xpath('/html/body/form/div[3]/main/div[2]/div[1]/div/div/div[1]/div/div[2]/div[1]/input').send_keys(agentRunContext.requestBody['username'])
		time.sleep(2)
		# to click on the Lösenord password
		driver.find_element_by_xpath('/html/body/form/div[3]/main/div[2]/div[1]/div/div/div[1]/div/div[2]/div[2]/div/input').send_keys(agentRunContext.requestBody['password'])
		time.sleep(2)
		# to click on the loggi button
		driver.find_element_by_xpath('/html/body/form/div[3]/main/div[2]/div[1]/div/div/div[1]/div/div[2]/input').click()
		# to select the Fakturor(Bills) button
		time.sleep(5)
		driver.find_element_by_xpath('/html/body/form/div[3]/div[1]/div/nav/div[2]/ul/li[4]').click()
		time.sleep(2)

		for i in range(0,20):
		    # to select the search button
		    #driver.execute_script(('window.scrollTo(0,200);'))
		    #time.sleep(3)
		    # driver.find_element_by_xpath("/html/body/form/div[3]/div/div[2]/div[2]/div[5]/div/div/button").click()
		    # time.sleep(2)

		    # driver.find_element_by_xpath('/html/body/form/div[3]/div/div[2]/div[2]/div[5]/div/ul/li/div/div/input').send_keys('Betald')
		    # time.sleep(2)
		    # driver.find_element_by_xpath("/html/body/form/div[3]/div/div[2]/div[2]/div[5]/div/ul/li/div/button[1]").click()

		    time.sleep(3)

		    countries=driver.find_elements_by_xpath('//tbody/tr/td[7]')
		    print(len(countries))
		    time.sleep(3)
		    try:
		        driver.find_element_by_class_name("notification-close").click()
		    except:
		        print("no pop element")
		    x=100
		    time.sleep(5)

		    #download pdf invoice
		    
		    print("start")
		    print(startlink)
		        
		    print("End")
		    print(len(countries))
		    for i in range(startlink,len(countries)+1):
		    #for i in range(1,5):
		        
		        time.sleep(5)
		        x+=30
		        driver.execute_script(('window.scrollTo(0, {0});'.format(x)))
		        time.sleep(10)
		        pdf_link=driver.find_element_by_xpath("/html/body/form/div[3]/main/div[3]/div[2]/div[1]/div/div/div/div[2]/div/table/tbody/tr["+str(i)+"]/td[7]/a")
		        betlad=driver.find_element_by_xpath("/html/body/form/div[3]/main/div[3]/div[2]/div[1]/div/div/div/div[2]/div/table/tbody/tr["+str(i)+"]/td[1]")
		        print(betlad.text)
		        print(pdf_link.text)
		        if pdf_link.text=='Ladda ner' and  betlad.text=='Betald':
		            driver.execute_script("arguments[0].setAttribute('download','')",pdf_link)
		            time.sleep(2)
		            pdf_link.click()
		            print(i) 
		            time.sleep(5)
		    startlink=len(countries)
		    
		    driver.find_element_by_xpath("/html/body/form/div[3]/main/div[3]/div[2]/div[5]/button").click()
		    
		    #driver.find_element_by_xpath("/html/body/form/div[3]/main/div[3]/div[2]/div[5]/button").click()
		    #reset=i

        





    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS, str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())

    driver.close()
    #os.rmdir(download_dir)





