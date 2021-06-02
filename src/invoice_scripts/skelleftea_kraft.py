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


def SkellefteaKraft(agentRunContext):
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

        driver.find_element_by_xpath('/html/body/app-root/main/section/div/mp-login-page/div/div/mp-login/div/div/div/div[3]').click()
        time.sleep(5)
        driver.execute_script('window.scrollTo(0,200);')
        time.sleep(5)
        driver.find_element_by_xpath("/html/body/app-root/main/section/div/mp-login-page/div/div/mp-login/div/div/div/div[4]/div[1]/div/input").send_keys(agentRunContext.requestBody['username'])

        driver.find_element_by_xpath("/html/body/app-root/main/section/div/mp-login-page/div/div/mp-login/div/div/div/div[4]/div[2]/div/input").send_keys(agentRunContext.requestBody['password'])

        driver.find_element_by_xpath("/html/body/app-root/main/section/div/mp-login-page/div/div/mp-login/div/div/div/div[4]/div[2]/button").click()
        time.sleep(5)

        driver.find_element_by_xpath("/html/body/app-root/div/mp-menu/header/div/div/div/nav/ul/li[3]").click()
        time.sleep(5)
        driver.find_element_by_xpath("/html/body/app-root/main/section/div/mp-economy-corporate-costs-page/div[2]/div/mp-tabs-menu/div/div[1]/ul/mp-tabs-menu-item[2]").click()
        time.sleep(5)

        driver.find_element_by_xpath("/html/body/app-root/main/section/div/mp-economy-corporate-invoices-page/div[3]/div[1]/mp-invoices/div/div/div/div[2]/div/select").click()
        time.sleep(5)
        driver.find_element_by_xpath("/html/body/app-root/main/section/div/mp-economy-corporate-invoices-page/div[3]/div[1]/mp-invoices/div/div/div/div[2]/div/select/option[4]").click()

        time.sleep(5)
        # able_tag=soup1.find_all("table",{"class":"table-default table-invoice responsive"})
        # print(Table_tag)
        countries = driver.find_elements_by_xpath('//tbody/tr/td[1]')
        print(len(countries))
        x = 80
        for i in range(1, len(countries)):
            time.sleep(5)
            x += 30
            driver.execute_script(('window.scrollTo(0, {0});'.format(x)))
            time.sleep(5)
            driver.find_element_by_xpath("/html/body/app-root/main/section/div/mp-economy-corporate-invoices-page/div[3]/div[1]/mp-invoices/div/div/table/tbody/tr[" + str(i) + "]/td[2]").click()
            print(i)
            time.sleep(5)





    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS, str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())

    driver.close()
    #os.rmdir(download_dir)





