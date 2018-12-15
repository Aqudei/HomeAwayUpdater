from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import yaml

# ORIGINAL PHONE NUMBER = '+1 419-234-4405'


def get_accounts():
    with open('./config.yaml', 'rt') as fp:
        config = yaml.load(fp)
        for account in config['accounts']:
            yield (account['username'], account['password'])


class HomeAwayUpdater:

    LOGIN_URL = 'https://cas.homeaway.com/auth/homeaway/login?service=https%3A%2F%2Fwww.homeaway.com%2Fhaod%2Fauth%2Fsignin.html'
    TARGET_PAGE_URL = 'https://www.homeaway.com/lm/{}/loc.html'
    PROPERTY_XPATH = '//*[@id="page-content"]/div/div/div[3]/table/tbody/tr/td/div/div[1]/span/a'
    MODAL_XPATH = "//div[@class='modal-content']/button"
    PROPERTY_LOC_XPATH = '//*[@id="displayPropertyMarker"]'
    SAVE_SETTING_XPATH = "//*[@id='listing']/div[1]/a[1]"
    SEND_VERIFICATION_XPATH = '//*[@id="form-submit"]'

    def __init__(self, credential_list, driver):
        self.driver = driver
        self.credential_list = credential_list

    def login(self, username, password):
        print('Now logging in...')
        self.driver.get(self.LOGIN_URL)

        username_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'username')))
        password_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'password')))

        username_field.send_keys(username)
        password_field.send_keys(password)

        password_field.submit()

    def __perform_2FA(self, username):
        try:
            print('Trying if 2FA is required...')
            phones_elements = WebDriverWait(self.driver, 32).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, '//*[contains(@id,"phoneId")]'))
            )

            send_verification_button = WebDriverWait(self.driver, 32).until(
                EC.presence_of_element_located(
                    (By.XPATH, self.SEND_VERIFICATION_XPATH))
            )

            send_verification_button.click()

            login_xpath = "//*[@id='form-submit']"
            login_button = WebDriverWait(self.driver, 32).until(
                EC.presence_of_element_located(
                    (By.XPATH, login_xpath))
            )

            code = input(
                'Please enter verification code for user {}: '.format(username))

            _2fa_code = self.driver.find_element_by_xpath("//*[@id='code']")
            _2fa_code.send_keys(code)
            login_button.click()

            print('2FA processing done.')
        except:
            print('No 2fA page required.')

    def get_property_urls(self):

        print('Now gathering the urls of properties...')

        rgx_property_id = re.compile(r'(\d+\.\d+\.\d+)$')

        properties = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, self.PROPERTY_XPATH)))
        hrefs = [p.get_attribute('href') for p in properties]
        for href in hrefs:
            _href = rgx_property_id.search(href)
            if _href:
                _href = self.TARGET_PAGE_URL.format(_href.group(1))
                yield _href

    def __try_close_modal(self):
        try:
            print('Looking for modal dialog...')
            close_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, self.MODAL_XPATH)))
            close_button.click()
            print('Modal dialog was closed!')
        except:
            print('No modal dialog was found!')

    def change_setting(self, url):

        print('Processing property: ' + url)

        self.driver.get(url)
        self.__try_close_modal()

        location_checkbox = WebDriverWait(self.driver, 32).until(
            EC.presence_of_element_located((By.XPATH, self.PROPERTY_LOC_XPATH))
        )

        if location_checkbox.is_selected():
            self.__try_close_modal()
            print('Location is displayed, Now turning off...')
            clickable = self.driver.find_element_by_xpath(
                '/html/body/div[2]/div[1]/div/div[2]/div[4]/form/div[3]/div/div[1]/div/div/div/label')
            # location_checkbox.click()
            self.driver.execute_script("arguments[0].click();", clickable)
            save_button = self.driver.find_element_by_xpath(
                self.SAVE_SETTING_XPATH)

            self.__try_close_modal()

            self.driver.execute_script("arguments[0].click();", save_button)
            # save_button.click()
            print('Settings save!')
            return

        print('Location is not displayed. No action needed.')

    def run_bot(self):
        for username, password in self.credential_list:
            print('\n\nProcessing account of : ' + username)
            self.login(username, password)
            self.__perform_2FA(username)
            urls = list(self.get_property_urls())

            print('Found the following property urls:')
            print('\n'.join(urls))

            for url in urls:
                self.change_setting(url)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()


def main():
    # driver = webdriver.PhantomJS(
    #     executable_path=r'C:\Users\Administrator\AppData\Local\Yarn\bin\phantomjs.cmd')

    driver = webdriver.Firefox()
    with HomeAwayUpdater(get_accounts(), driver) as bot:
        bot.run_bot()


if __name__ == '__main__':
    main()
