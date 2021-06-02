from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from datetime import date
import os
import traceback
import threading

from common import get_driver
from common import Log
import config


def convert_to_datetime(date_string):
    return date(*map(int, date_string.split('-')))


def UmeaEnergi(agentRunContext):

    log = Log(agentRunContext)

    log.job(config.JOB_RUNNING_STATUS,'UmeaEnergi thread started execution')

    if not {'startDate', 'endDate'} <= set(agentRunContext.requestBody):
            log.job(config.JOB_COMPLETED_FAILED_STATUS, 'Request missing parameters, Period not specified')
            return

    try:

        url = 'https://www.umeaenergi.se/mina-sidor/login'
        thread_id = str(threading.get_ident())
        download_dir = os.path.join(os.getcwd(),'invoices','temp-'+thread_id)

        driver = get_driver(download_dir)
        driver.maximize_window()
        driver.get(url)

        wait = WebDriverWait(driver,10)
        time.sleep(5)
        wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div/div[3]/div/div/div[2]/div/div/button')))
        driver.find_element_by_xpath('/html/body/div/div[3]/div/div/div[2]/div/div/button').click()

        log.info('Accepted Cookies')

        driver.find_element_by_id('sectionplaceholder_1_rowplaceholderec931a9bef844079a92fd532f121cae1_0_blockplaceholder1013ddee3ff2e4f9383371ec262ea3ef1_0_Login1_UserName').send_keys(agentRunContext.requestBody['username'])
        driver.find_element_by_id('sectionplaceholder_1_rowplaceholderec931a9bef844079a92fd532f121cae1_0_blockplaceholder1013ddee3ff2e4f9383371ec262ea3ef1_0_Login1_Password').send_keys(agentRunContext.requestBody['password'])
        driver.find_element_by_id('sectionplaceholder_1_rowplaceholderec931a9bef844079a92fd532f121cae1_0_blockplaceholder1013ddee3ff2e4f9383371ec262ea3ef1_0_Login1_LoginButton').click()

        wait = WebDriverWait(driver,20)

        try:
            wait.until(presence_of_element_located((By.XPATH,'//*[@id="statistics"]/div[2]/div[1]/div/div[2]/div[2]/a[1]')))
        except TimeoutException:
            log.job(config.JOB_COMPLETED_FAILED_STATUS,'Not able to login, wrong username or password')
            return

        log.job(config.JOB_RUNNING_STATUS,'Logged in')

        time.sleep(40)

        driver.find_elements_by_xpath("/html/body/form/div[3]/div[3]/div/div[4]/ul/li[2]/a")[0].click()
        js = "var aa=document.getElementById('onetrust-consent-sdk');aa.parentNode.removeChild(aa)"
        driver.execute_script(js)
        time.sleep(5)

        wait.until(presence_of_element_located((By.XPATH,'/html/body/form/div[4]/div[3]/div[1]/div[2]/div[1]/div/div[4]/div[2]/div[2]/a')))
        driver.find_element_by_xpath('/html/body/form/div[4]/div[3]/div[1]/div[2]/div[1]/div/div[4]/div[2]/div[2]/a').click()

        time.sleep(10)
        driver.execute_script(js)
        time.sleep(5)

        start_date = convert_to_datetime(agentRunContext.requestBody['startDate'])
        end_date = convert_to_datetime(agentRunContext.requestBody['endDate'])

        page_list = driver.find_element_by_xpath("/html/body/form/div[3]/div[2]/div[1]/div/div[1]/div[2]/div/div/div[4]/div[2]/div[1]/div/div/ul")
        pages = page_list.find_elements_by_tag_name("li")

        files_downloaded = 0

        for page in pages:
            page.find_element_by_xpath(".//a").click()
            time.sleep(5)
            driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
            table = driver.find_element_by_xpath("//table[@class='table table-bordered data-table bg-white']")
            rows = table.find_elements_by_xpath(".//tr")
            rows.pop(0)
            curr_page_start_date = convert_to_datetime(rows[0].find_elements_by_xpath(".//td")[5].text)
            if curr_page_start_date < start_date:
                break
            curr_page_end_date = convert_to_datetime(rows[-1].find_elements_by_xpath(".//td")[5].text)
            if (curr_page_start_date >= start_date >= curr_page_end_date) or (curr_page_start_date >= end_date >= curr_page_end_date) or (start_date <= curr_page_start_date <= end_date):
                for row in rows:
                    driver.execute_script("window.scrollTo(0, window.scrollY + 20)")
                    cells = row.find_elements_by_xpath(".//td")
                    curr_row_date = convert_to_datetime(cells[5].text)
                    if cells[4].text=='Betald' and (start_date <= curr_row_date <= end_date):
                        cells[0].click()
                        time.sleep(5)
                        if len(os.listdir(download_dir)) > files_downloaded:
                            files_downloaded += 1
                        else:
                            log.info('Download failed for invoice {0}'.format(cells[1].text))

        log.job(config.JOB_RUNNING_STATUS,'Successfully downloaded {0} invoices'.format(files_downloaded))
    except Exception as e:
        log.exception(traceback.format_exc())
        log.job(config.JOB_COMPLETED_FAILED_STATUS,e)