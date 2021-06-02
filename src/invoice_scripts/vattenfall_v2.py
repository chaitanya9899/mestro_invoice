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


def Vattenfall_v2(agentRunContext):
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

        # to press the private button in login tab
        wait.until(presence_of_element_located((By.XPATH, '//*[@id="nav-login"]/ul/li[1]/a')))
        driver.find_element_by_xpath('//*[@id="nav-login"]/ul/li[1]/a').click()

        # to open the username tab
        wait.until(presence_of_element_located((By.XPATH, '//*[@id="customerNumTab"]/a')))
        driver.find_element_by_xpath('//*[@id="customerNumTab"]/a').click()

        # to enter the username
        driver.find_element_by_id('customerId').send_keys(agentRunContext.requestBody['username'])

        # to enter the password
        driver.find_element_by_id("pin").send_keys(agentRunContext.requestBody['password'])

        # to press the login buttom
        driver.find_element_by_id('submitButton2').click()

        # to open the Min förbrukning
        wait.until(presence_of_element_located((By.XPATH ,'//*[@id="collapse-8769"]/div/ul/li[2]/a')))
        driver.find_element_by_xpath('//*[@id="collapse-8769"]/div/ul/li[2]/a').click()
        sleep(10)

        #driver.find_element_by_xpath('/html/body/div[5]/cm-premise-dir/section/div/div/div/div/div/div/button/span[1]').click()
        driver.find_element_by_xpath('/html/body/div[5]/premise-filter/premise-large-filter/div[2]/div/div/div/div/button').click()
        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')
        sleep(5)
        page_source = driver.page_source
        soup1 = BeautifulSoup(page_source, 'lxml')
        type(soup1)
        #bs4.BeautifulSoup





        select_tag=soup1.find("table",{"class":"select-menu__table"})
        tbody_tag=select_tag.find("tbody")
        tr_tag=tbody_tag.find_all("tr")
        #td_tag=tr_tag.find('td')
        #td_tag.text

        sleep(5)
        #driver.find_element_by_css_selector("body > section > div > div > div > div.alertblock > div > div > div > div.link > a > span").click()


        sleep(5)
        print(len(tr_tag))



        x=500

        for j in range(0,len(tr_tag)):
            driver.find_element_by_xpath('/html/body/div[5]/premise-filter/premise-large-filter/div[2]/section/div[3]/div/div/table/tbody/tr['+str(j+1)+']').click()
            sleep(2)
            print(j+1)
            driver.find_element_by_xpath('/html/body/div[5]/premise-filter/premise-large-filter/div[2]/section/div[1]/div/div/div[1]/button').click()
            driver.execute_script(('window.scrollTo(0,400);'))
            sleep(2)
            driver.find_element_by_css_selector("body > section > div > div > div > div.myinvoicesblock > my-invoice-component > div > div > div > div.row.marb20.space-filter > div.col-lg-6.hidden-sm.hidden-xs > div > div > button:nth-child(2)").click()
            page_source = driver.page_source
            soup1 = BeautifulSoup(page_source, 'lxml')

            #bs4.BeautifulSoup
            Table_tag=soup1.find_all("table",{"class":"table invoice-tab"})[0]
            tbody_tag1=Table_tag.find_all("tbody",{"class":"inv-head"})
            sleep(5)
            print(len(tbody_tag))
            log.job(config.JOB_RUNNING_STATUS,'Started downloading invoices')
            sleep(2)
            
            for i in range(4,len(tbody_tag1)):
                sleep(5)
                x+=80
                driver.execute_script(('window.scrollTo(0, {0});'.format(x)))
                sleep(2)
                driver.find_element_by_css_selector("body > section > div > div > div > div.myinvoicesblock > my-invoice-component > div > div > div > div:nth-child(3) > div > div > table > tbody:nth-child("+str(i)+") > tr.inv-tr-head.hidden-xs > td.icons-invoice").click()
                print(i)
                sleep(2)

                try:
                    if i is 2:
                        #pop button
                        driver.find_element_by_css_selector("body > div._hj-widget-container._hj-widget-theme-dark > div > div > div > div > button").click()
                        sleep(2)
                except:
                    print("no pop element")

                #button
                driver.find_element_by_css_selector("body > section > div > div > div > div.myinvoicesblock > my-invoice-component > div > div > div > div:nth-child(3) > div > div > table > tbody.inv-head.inv_detail_container_allpaid.inv_detail_open > tr.inv-tr-body > td > div > div:nth-child(2) > div.col-md-2.col-sm-3.col-xs-12.order4-sm.inv-add-list.flex-push-right > div > button > span:nth-child(1)").click()
                sleep(5)  

            sleep(2)
            driver.execute_script(('window.scrollTo(0,-400);'))
            sleep(5)
            x=500
            #click drop down list
            driver.find_element_by_css_selector('body > div.premise-wrapper--in-title > premise-filter > premise-large-filter > div:nth-child(2) > div > div > div > div > button').click()
            #driver.execute_script(('window.scrollTo(0,400);'))
            sleep(5)
 
        
    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())
    
    driver.close()
    os.rmdir(download_dir)
