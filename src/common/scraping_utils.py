from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from pathlib import Path
import os
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

chrome_path = r'C:\Users\Dhanvi\Headless_Browsers\chromedriver-90'

def enable_download_headless(browser,download_dir):
    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd':'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
    browser.execute("send_command", params)

def get_driver(temp_directory):
    chrome_options = Options()
    d = DesiredCapabilities.CHROME
    d['goog:loggingPrefs'] = { 'browser':'ALL' }
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--verbose')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_experimental_option("prefs", {
            "download.default_directory": str(os.path.join(Path.home(), "Downloads")),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
            "safebrowsing.enabled": False
    })
    driver = webdriver.Chrome(options=chrome_options,desired_capabilities=d)
    Path(temp_directory).mkdir(parents=True,exist_ok=True)
    download_dir = os.path.join(temp_directory)
    enable_download_headless(driver, download_dir)
    return driver