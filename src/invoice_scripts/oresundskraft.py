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




def Oresundskraft(agentRunContext):
	print(agentRunContext.homeURL)
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

        driver.find_element_by_class_name("cc-compliance").click()
        driver.find_element_by_xpath("/html/body/div[3]/div/div[1]/div/div[2]/div[2]/div[1]/input").send_keys(agentRunContext.requestBody['username'])
        driver.find_element_by_xpath("/html/body/div[3]/div/div[1]/div/div[2]/div[2]/div[2]/input").send_keys(agentRunContext.requestBody['password'])
        driver.find_element_by_xpath("/html/body/div[3]/div/div[1]/div/div[2]/div[3]/div[1]/button").click()
        time.sleep(10)
        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')
        driver.execute_script(('window.scrollTo(0,50);'))
        startlink=1
        time.sleep(5)
        driver.find_element_by_xpath('/html/body/div[2]/div[2]/div[4]/div[2]/div/div[1]/div[2]/div[2]/div[2]/div/div[2]/div/ul/li[1]').click()
        time.sleep(5)
		x=100
		log.job(config.JOB_RUNNING_STATUS,'Started downloading invoices')
		for i in range(0,30):    
		    items=driver.find_element_by_xpath('/html/body/div[2]/div[2]/div[4]/div[2]/div/div[4]')
		    #ad=items.find_element_by_class_name('listing-container')
		    new=items.find_elements_by_tag_name('li')
		    print(len(new))
		    time.sleep(5)
		    print("start")
		    print(startlink)
		    print("End")
		    for i in range(startlink,len(new)+1):
		        Betald=driver.find_element_by_xpath('/html/body/div[2]/div[2]/div[4]/div[2]/div/div[4]/div[2]/ul/li['+str(i)+']/div/div/div[5]')
		        print(Betald.text)
		        print(i)
		        #x+=80
		        #driver.execute_script(('window.scrollTo(0, {0});'.format(x)))

		        if Betald.text =='Betald':
		            driver.find_element_by_xpath("/html/body/div[2]/div[2]/div[4]/div[2]/div/div[4]/div[2]/ul/li["+str(i)+"]/div/div/div[5]").click()
		            pdf_link=driver.find_element_by_xpath("/html/body/div[2]/div[2]/div[4]/div[2]/div/div[4]/div[2]/ul/li["+str(i)+"]/div/div/div[7]/div[6]/div/span/a")
		            print(pdf_link)
		            driver.execute_script("arguments[0].setAttribute('download','')",pdf_link)
		            time.sleep(5)
		            pdf_link.click()
		            time.sleep(5)
		            driver.execute_script(('window.scrollTo(0,30);'))
		    ## append value of list
		    startlink=len(new)
		    ##click for next button
		    try:
		        driver.find_element_by_xpath("/html/body/div[2]/div[2]/div[4]/div[2]/div/div[4]/div[2]/div[2]/div/div/span").click()
		    except:
		        print("Completed")

    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())
    
    driver.close()
    #os.rmdir(download_dir)


