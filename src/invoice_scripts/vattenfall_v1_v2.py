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
from bs4 import BeautifulSoup


from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from calendar import monthrange


from common import get_driver
from common import Log
import config

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

        #agentRunContext.requestBody['username']
        #agentRunContext.requestBody['password']
        #to accept the cookies
        driver.find_element_by_id("cmpwelcomebtnyes").click()
        # to press the login button
        driver.find_element_by_xpath('//*[@id="page-header"]/div/nav/div/div/ul[2]/li[1]/a').click()
        wait = WebDriverWait(driver, 45)
        driver.find_element_by_xpath('/html/body/header/div/nav/div/div/ul[2]/li[1]/div/ul/li[1]').click()
        time.sleep(5)

        driver.find_element_by_xpath("/html/body/div[1]/div/div/div/div/ul/li[3]").click()
        time.sleep(5)


        # to enter the username
        driver.find_element_by_id('customerId').send_keys(agentRunContext.requestBody['username'])

        # to enter the password
        driver.find_element_by_id("pin").send_keys(agentRunContext.requestBody['password'])

        # to press the login buttom
        driver.find_element_by_id('submitButton2').click()
        
        

        driver.find_element_by_xpath('//*[@id="collapse-8769"]/div/ul/li[1]/a').click()
        time.sleep(10)

        driver.find_element_by_xpath('/html/body/header/div/div/ul[1]/li[15]/div/ul/li[2]').click()
        time.sleep(10)
        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')
        driver.execute_script(('window.scrollTo(0,100);'))

        time.sleep(5)



        #driver.execute_script(('window.scrollTo(0,250);'))
        time.sleep(2)

        x=300
        for j in range(1,6):
            if j<=3:
                driver.find_element_by_xpath("/html/body/div[5]/premise-filter/premise-small-filter/div/div[1]/div/slick/div/div/div["+str(j)+"]").click()
                print(j)
                time.sleep(5)


                #sleep(5)
                #driver.execute_script(('window.scrollTo(0,500);'))
                #x=80
                driver.find_element_by_css_selector("body > section > div > div > div > div.myinvoicesblock > my-invoice-component > div > div > div > div.row.marb20.space-filter > div.col-lg-6.hidden-sm.hidden-xs > div > div > button:nth-child(3)").click()
                time.sleep(2)

                page_source = driver.page_source
                soup1 = BeautifulSoup(page_source, 'lxml')

                #bs4.BeautifulSoup
                Table_tag=soup1.find_all("table",{"class":"table invoice-tab"})[0]
                tbody_tag=Table_tag.find_all("tbody",{"class":"inv-head"})
                time.sleep(5)
                #tr_tag=tbody_tag.find_all("tr",{"class":"inv-tr-head hidden-xs"})
                #td_tag=tr_tag.find_all("td",{"class":"icons-invoice"})
                print(len(tbody_tag)) 
                #sleep(5)
                
                log.job(config.JOB_RUNNING_STATUS,'Started downloading invoices')
                for i in range(2,len(tbody_tag)):
                    #td_tag1=tr_tag[i].find_all("td")
                    time.sleep(5)
                    x+=80
                    driver.execute_script(('window.scrollTo(0, {0});'.format(x)))
                    time.sleep(5)
                    driver.find_element_by_css_selector("body > section > div > div > div > div.myinvoicesblock > my-invoice-component > div > div > div > div:nth-child(3) > div > div > table > tbody:nth-child("+str(i+1)+") > tr.inv-tr-head.hidden-xs > td.icons-invoice").click()
                    time.sleep(5)

                    try:
                        if i is 2:
                            #pop button
                            driver.find_element_by_css_selector("body > div._hj-widget-container._hj-widget-theme-dark > div > div > div > div > button").click()
                            time.sleep(5)
                    except:
                        print("no pop element")
                    

                    #button
                    driver.find_element_by_css_selector("body > section > div > div > div > div.myinvoicesblock > my-invoice-component > div > div > div > div:nth-child(3) > div > div > table > tbody.inv-head.inv_detail_container_allpaid.inv_detail_open > tr.inv-tr-body > td > div > div:nth-child(2) > div.col-md-2.col-sm-3.col-xs-12.order4-sm.inv-add-list.flex-push-right > div > button > span:nth-child(1)").click()
                    time.sleep(5)

                driver.execute_script('window.scrollTo(0,80)')
                time.sleep(5)
                x=300




                    #print(td_tag1)
            else:
                driver.find_element_by_xpath("/html/body/div[5]/premise-filter/premise-small-filter/div/div[1]/div/slick/button[2]").click()
                time.sleep(5)

                driver.find_element_by_xpath("/html/body/div[5]/premise-filter/premise-small-filter/div/div[1]/div/slick/div/div/div["+str(j)+"]").click()
                time.sleep(5)

                driver.find_element_by_css_selector("body > section > div > div > div > div.myinvoicesblock > my-invoice-component > div > div > div > div.row.marb20.space-filter > div.col-lg-6.hidden-sm.hidden-xs > div > div > button:nth-child(3)").click()
                time.sleep(5)

                page_source = driver.page_source
                soup1 = BeautifulSoup(page_source, 'lxml')
                #bs4.BeautifulSoup
                Table_tag=soup1.find_all("table",{"class":"table invoice-tab"})[0]
                tbody_tag=Table_tag.find_all("tbody",{"class":"inv-head"})
                time.sleep(5)

                #tr_tag=tbody_tag.find_all("tr",{"class":"inv-tr-head hidden-xs"})
                #td_tag=tr_tag.find_all("td",{"class":"icons-invoice"})
                print(len(tbody_tag)) 
                time.sleep(5)

                
                log.job(config.JOB_RUNNING_STATUS,'Started downloading invoices')
                #download invoices pdf
                for i in range(2,len(tbody_tag)):
                    #td_tag1=tr_tag[i].find_all("td")

                    time.sleep(5)
                    x+=80
                    driver.execute_script(('window.scrollTo(0, {0});'.format(x)))
                    time.sleep(5)
                    driver.find_element_by_css_selector("body > section > div > div > div > div.myinvoicesblock > my-invoice-component > div > div > div > div:nth-child(3) > div > div > table > tbody:nth-child("+str(i+1)+") > tr.inv-tr-head.hidden-xs > td.icons-invoice").click()
                    time.sleep(5)

                    try:
                        if i is 2:
                            #pop button
                            driver.find_element_by_css_selector("body > div._hj-widget-container._hj-widget-theme-dark > div > div > div > div > button").click()
                            time.sleep(5)

                    except:
                        print("no pop element")



                    #button

                    driver.find_element_by_css_selector("body > section > div > div > div > div.myinvoicesblock > my-invoice-component > div > div > div > div:nth-child(3) > div > div > table > tbody.inv-head.inv_detail_container_allpaid.inv_detail_open > tr.inv-tr-body > td > div > div:nth-child(2) > div.col-md-2.col-sm-3.col-xs-12.order4-sm.inv-add-list.flex-push-right > div > button > span:nth-child(1)").click()
                    time.sleep(5)

                driver.execute_script('window.scrollTo(0,80)')
                time.sleep(5)

                x=300



    except Exception as e:
         log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
         log.exception(traceback.format_exc())
         print(traceback.format_exc())

    driver.close()
            # os.rmdir(download_dir)


