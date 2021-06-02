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
from bs4 import BeautifulSoup


from common import get_driver
from common import Log
import config

def Eforsyning(agentRunContext):
    
	log = Log(agentRunContext)
    
	try:
		log.job(config.JOB_RUNNING_STATUS,'{0} thread started execution'.format(agentRunContext.requestBody['agentId']))
		thread_id = str(threading.get_ident())
		download_dir = os.path.join(os.getcwd(),'temp','temp-'+thread_id)
		print(download_dir)
		log.info('{0} with threadID {1} has its temp directory in {2}'.format(agentRunContext.requestBody['agentId'],thread_id,download_dir))
		driver = get_driver(download_dir)
		driver.maximize_window()
        #driver.get(agentRunContext.homeURL)
		driver.get(agentRunContext.requestBody['targetURL'])
		wait = WebDriverWait(driver, 100)
		time.sleep(3)
		##pop up element click
		try:
			driver.find_element_by_xpath('/html/body/div[2]/div[2]/div/mat-dialog-container/dff-cookie-consent-dialog/div/div/mat-dialog-actions/div/button[1]/span[1]').click()
		except:
			print("no pop up element")

		time.sleep(3)
		# to click on the Användarnamn username
		driver.find_element_by_id('forbrugerNr').send_keys(agentRunContext.requestBody['username'])
		# to click on the Lösenord password
		driver.find_element_by_id('kode').send_keys(agentRunContext.requestBody['password'])
		# to click on the loggi button
		#wait.until(presence_of_element_located((By.XPATH, '/html/body/form/div[4]/div/div[2]/div[3]/div/div[1]/div[2]/div/div[2]/div[4]/div/div[1]/div/input')))
		driver.find_element_by_xpath('/html/body/div[1]/div[2]/app-root/app-shell/div/div/div/div/login/login-container/div[2]/div[2]/mat-tab-group/div/mat-tab-body[1]/div/login-forbrugernr/form/div[3]/button/span[1]').click()
		# to select the Fakturor(Bills) button
		time.sleep(10)

        #pop up element click
		try:
		    driver.find_element_by_css_selector("#button-spoerg-mig-senere > span.mat-button-wrapper").click()
		except:
		    print("no pop element")
		time.sleep(10)

		driver.find_element_by_xpath('/html/body/div[1]/div[2]/app-root/app-shell/div/eforsyning-sidenav-menu/dff-sidenav-menu/div[3]/a').click()
		time.sleep(5)
		# to select the search button

		driver.execute_script(('window.scrollTo(0,200);'))
		time.sleep(3)

		# getting page data
		page_source = driver.page_source
		soup1 = BeautifulSoup(page_source, 'lxml')

		#table content
		PDF_tag=soup1.find_all("table",{"class":"mat-table cdk-table mat-elevation-z2 ng-star-inserted"})[0]
		tr_tag=PDF_tag.find_all("tr")
		print(len(tr_tag))



		## create pdf file in folder
		def pdfdownload(url,filename):
		    pdf_path =url 
		    r = requests.get(url, stream=True)
		    #file = open(r"H:/new/pdf/"+filename+".pdf", 'wb')
		    file=os.path.join(download_dir,filename+'.pdf','wb')
		    file.write(r.content)
		    file.close()
		        
		##scraping table content get href link
		for i in range(1,len(tr_tag)):
		    td_tag=tr_tag[i].find_all("td")[0]
		    a_tag_url=td_tag.find("a")["href"]
		    document=td_tag.text
		    print(document)
		    pdfdownload(a_tag_url,document)
		    print(a_tag_url)


	except Exception as e:
		log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
		log.exception(traceback.format_exc())
		print(traceback.format_exc())
    
	driver.close()
	os.rmdir(download_dir)
