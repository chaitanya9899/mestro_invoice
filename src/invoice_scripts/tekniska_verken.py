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

def TekniskaVerken(agentRunContext):
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
        
        # to accept cookies
        driver.find_element_by_xpath('/html/body/div[1]/div[2]/div/button').click()
        wait = WebDriverWait(driver, 60)

        time.sleep(3)
        def pdfdownload(url, filename):
            import requests
            # url='https://pdfs.semanticscholar.org/c029/baf196f33050ceea9ecbf90f054fd5654277.pdf'
            pdf_path = "https://www.tekniskaverken.se" + url
            r = requests.get(pdf_path)

            with open(r"/home/test/Downloads/" + filename + ".pdf", 'wb') as f:
                f.write(r.content)
        #
        # def pdfdownload(url,filename):
        #     import urllib.request
        #     pdf_path = "https://www.tekniskaverken.se/" + url  # "http://distcourts.tap.nic.in/hcorders/2014/arbappl/arbappl_132_2014.pdf"
        #     print(url)
        #
        #     response = urllib.request.urlopen(pdf_path)
        #     file = open(r"/home/test/Downloads/" + filename + ".pdf", 'wb')
        #     file.write(response.read())
            # file.close()
            #
            # import pikepdf
            #
            # file_path = '/home/test/Downloads/'
            # pdf = pikepdf.open(file_path, allow_overwriting_input=True)
            # pdf.save('/home/test/Downloads/saved.pdf')

        # To signin
        # Click on Foretag(Bussiness)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/header/div[2]/div/form/div[2]/button[2]')))
        driver.find_element_by_xpath('/html/body/header/div[2]/div/form/div[2]/button[2]').click()

        time.sleep(3)
        # To type Kundnummer(customer number)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/header/div[2]/div/form[2]/ul/li[1]/input')))
        driver.find_element_by_xpath('/html/body/header/div[2]/div/form[2]/ul/li[1]/input').send_keys(agentRunContext.requestBody['username'])

        time.sleep(3)

        # to type  Lösenord (password)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/header/div[2]/div/form[2]/ul/li[2]/input')))
        driver.find_element_by_xpath('/html/body/header/div[2]/div/form[2]/ul/li[2]/input').send_keys(agentRunContext.requestBody['password'])

        time.sleep(3)

        # to click on Logga  in (login)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/header/div[2]/div/form[2]/ul/li[3]/input')))
        driver.find_element_by_xpath('/html/body/header/div[2]/div/form[2]/ul/li[3]/input').click()

        time.sleep(3)
        
        log.job(config.JOB_RUNNING_STATUS,'Logged in successfully')

        # To click on Välj konto (choose account)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/main/div/main/div/table/tbody/tr[1]/td[5]/a')))
        driver.find_element_by_xpath('/html/body/main/div/main/div/table/tbody/tr[1]/td[5]/a').click()

        # to select Se Mina Fakturor(See my Invoices)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/div[3]/div[1]/a[4]')))
        driver.find_element_by_xpath('/html/body/div[3]/div[1]/a[4]').click()

        # to select Fr.O.M(From date)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/main/div/main/div/div[2]/div[1]/div/div[1]/input[1]')))
        driver.find_element_by_xpath('/html/body/main/div/main/div/div[2]/div[1]/div/div[1]/input[1]').clear()
        driver.find_element_by_xpath('/html/body/main/div/main/div/div[2]/div[1]/div/div[1]/input[1]').send_keys('2020-01-01')

        # to select T.O.M(To date)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/main/div/main/div/div[2]/div[2]/div/div[1]/input[1]')))
        driver.find_element_by_xpath('/html/body/main/div/main/div/div[2]/div[2]/div/div[1]/input[1]').clear()
        driver.find_element_by_xpath('/html/body/main/div/main/div/div[2]/div[2]/div/div[1]/input[1]').send_keys('2021-01-02')

        # to select status as Betald(paid)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/main/div/main/div/div[2]/div[4]/div/div/button')))
        driver.find_element_by_xpath('/html/body/main/div/main/div/div[2]/div[4]/div/div/button').click()

        wait.until(presence_of_element_located((By.XPATH,'/html/body/main/div/main/div/div[2]/div[4]/div/div/ul/li[2]/a')))
        driver.find_element_by_xpath('/html/body/main/div/main/div/div[2]/div[4]/div/div/ul/li[2]/a').click()

        # to download the invoices (visa/show)

        time.sleep(5)
        # page_source = driver.page_source
        # soup1 = BeautifulSoup(page_source, 'html.parser')
        # type(soup1)
        # bs4.BeautifulSoup
        # title = soup1.title
        #
        # PDF_file_Table_tag = soup1.find_all("table", {"class": "mypages-invoice-list"})[0]
        #
        # tr_tag = PDF_file_Table_tag.find_all("tr")
        # print(len(tr_tag))
        #
        # chromeOptions=webdriver.ChromeOptions()
        # prefs = {"plugins.always_open_pdf_externally": True}
        # chromeOptions.add_experimental_option("prefs",prefs)
        # # driver=webdriver.Chrome()
        # # driver.get("https://www.tekniskaverken.se")
        # WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH,"//html/body/main/div/main/div/div[3]/table/tbody/tr[1]/td[6]/a"))).click()
        # WebDriverWait(driver,15).until(EC.number_of_windows_to_be(2))
        # driver.switch_to.window(driver.window_handles[-1])
        # WebDriverWait(driver,15).until(EC.element_to_be_clickable((By.XPATH,"//input[@value='Agree and proceed']"))).click()

        # PDF_file_Table_tag = driver.find_elements((By.XPATH('/html/body/main/div/main/div/div[3]/table')))[0].click()
        # tr_tag = PDF_file_Table_tag.find_elements("tr")
        # print(len(tr_tag))

        # driver.find_element(By.XPATH('//*[@id="/html/body/main/div/main/div/div[3]/table/tbody/tr[1]/td[6]/a"]')).click()
        log.job(config.JOB_RUNNING_STATUS,'Started downloading invoices')
        
        PDF_file_Table_tag = driver.find_element_by_class_name('mypages-invoice-list')
        body = PDF_file_Table_tag.find_element_by_tag_name("tbody")
        rows = body.find_elements_by_tag_name('tr')
        for row in rows:
            a_td = row.find_elements_by_tag_name('td')[-1].find_element_by_tag_name('a')
            driver.execute_script("arguments[0].setAttribute('download','')",a_td)
            time.sleep(2)
            a_td.click()
        # # rows = PDF_file_Table_tag.find_element_by_tag_name("tr")
        # columns =PDF_file_Table_tag.find_element_by_tag_name("td")
        # # for cell in columns: driver.find_element(By.LINK_TEXT("20")).click()
        # tr_tag = PDF_file_Table_tag.find_elements("tr")
        # print(len(tr_tag))

        # index=1
        #
        #
        # while(1):
        #     # To click on waste addresses
        #     # driver.find_element_by_xpath('/html/body/div[2]/div[1]/div/button').click()
        #
        #     time.sleep(3)
        #     try:
        #         driver.find_element_by_xpath('/html/body/main/div/main/div/div[3]/table/tbody/tr[1]/td[6]/a'.format(index)).click()
        #     #
        #     except Exception as e:
        #         # driver.find_element_by_xpath('/html/body/div[2]/div[1]/div/button').click()
        #         print(e)
        #         break

        #
        # for i in range(2, len(tr_tag)):

            # td_tag1 = tr_tag[i].find_all("td")[0]
            # td_tag2 = tr_tag[i].find_all("td")[1]
            # td_tag3 = tr_tag[i].find_all("td")[2]
            # td_tag4 = tr_tag[i].find_all("td")[3]
            # td_tag5 = tr_tag[i].find_all("td")[4]
            # td_tag6 = tr_tag[i].find_all("td")[5]

            # td_tag = tr_tag[i].find_elements("td")[5]
            # td_tag1 = tr_tag[i].find_elements("td")[1]
            # document = td_tag1.text
            #
            #
            # # document = td_tag3.text
            # print(document)
            #
            # # try:
            # a_tag_url = td_tag.find("a")["href"]
            # tag = a_tag_url
            # pdfdownload(tag, document)
            # print(tag)



            # except:
            #     print("No Document")

        time.sleep(5)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/main/div/main/div/div[3]/table/tbody/tr[1]/td[6]/a')))
        driver.find_element_by_xpath('/html/body/main/div/main/div/div[3]/table/tbody/tr[1]/td[6]/a').click()
        time.sleep(5)
        #to download pdfs
        wait.until(presence_of_element_located((By.XPATH,'/html/body/pdf-viewer//viewer-pdf-toolbar-new//div/div[3]/viewer-download-controls//cr-icon-button//div/iron-icon')))
        driver.find_element_by_xpath('/html/body/pdf-viewer//viewer-pdf-toolbar-new//div/div[3]/viewer-download-controls//cr-icon-button//div/iron-icon').click()

        time.sleep(5)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/main/div/main/div/div[3]/table/tbody/tr[2]/td[6]/a')))
        driver.find_element_by_xpath('/html/body/main/div/main/div/div[3]/table/tbody/tr[2]/td[6]/a').click()
        time.sleep(5)
        #to download pdfs
        wait.until(presence_of_element_located((By.XPATH,'/html/body/pdf-viewer//viewer-pdf-toolbar-new//div/div[3]/viewer-download-controls//cr-icon-button//div/iron-icon')))
        driver.find_element_by_xpath('/html/body/pdf-viewer//viewer-pdf-toolbar-new//div/div[3]/viewer-download-controls//cr-icon-button//div/iron-icon').click()

        time.sleep(5)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/main/div/main/div/div[3]/table/tbody/tr[3]/td[6]/a')))
        driver.find_element_by_xpath('/html/body/main/div/main/div/div[3]/table/tbody/tr[3]/td[6]/a').click()
        time.sleep(5)
        #to download pdfs
        wait.until(presence_of_element_located((By.XPATH,'/html/body/pdf-viewer//viewer-pdf-toolbar-new//div/div[3]/viewer-download-controls//cr-icon-button//div/iron-icon')))
        driver.find_element_by_xpath('/html/body/pdf-viewer//viewer-pdf-toolbar-new//div/div[3]/viewer-download-controls//cr-icon-button//div/iron-icon').click()

        time.sleep(5)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/main/div/main/div/div[3]/table/tbody/tr[4]/td[6]/a')))
        driver.find_element_by_xpath('/html/body/main/div/main/div/div[3]/table/tbody/tr[4]/td[6]/a').click()
        time.sleep(5)
        #to download pdfs
        wait.until(presence_of_element_located((By.XPATH,'/html/body/pdf-viewer//viewer-pdf-toolbar-new//div/div[3]/viewer-download-controls//cr-icon-button//div/iron-icon')))
        driver.find_element_by_xpath('/html/body/pdf-viewer//viewer-pdf-toolbar-new//div/div[3]/viewer-download-controls//cr-icon-button//div/iron-icon').click()

        time.sleep(5)
        wait.until(presence_of_element_located((By.XPATH,'/html/body/main/div/main/div/div[3]/table/tbody/tr[1]/td[6]/a')))
        driver.find_element_by_xpath('/html/body/main/div/main/div/div[3]/table/tbody/tr[6]/td[6]/a').click()
        time.sleep(5)
        #to download pdfs
        wait.until(presence_of_element_located((By.XPATH,'/html/body/pdf-viewer//viewer-pdf-toolbar-new//div/div[3]/viewer-download-controls//cr-icon-button//div/iron-icon')))
        driver.find_element_by_xpath('/html/body/pdf-viewer//viewer-pdf-toolbar-new//div/div[3]/viewer-download-controls//cr-icon-button//div/iron-icon').click()



            # index+= 1

        # /html/body/main/div/main/div/div[3]/table/tbody/tr[1]/td[6]

        #/html/body/pdf-viewer//viewer-pdf-toolbar-new//div/div[3]/viewer-download-controls//cr-icon-button//div
        # /html/body/pdf-viewer//viewer-pdf-toolbar-new//div/div[3]/viewer-download-controls//cr-icon-button//div
        # /html/body/pdf-viewer//viewer-pdf-toolbar-new//div/div[3]/viewer-download-controls//cr-icon-button//div/iron-icon

        # /html/body/main/div/main/div/div[3]/table/tbody/tr[1]/td[6]/a
        # /html/body/main/div/main/div/div[3]/table/tbody/tr[2]/td[6]/a
        
    except Exception as e:
        log.job(config.JOB_COMPLETED_FAILED_STATUS,str(e))
        log.exception(traceback.format_exc())
        print(traceback.format_exc())
    
    driver.close()
    os.rmdir(download_dir)
