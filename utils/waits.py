from selenium.webdriver.support.ui import WebDriverWait

DEFAULT_TIMEOUT = 15

def build_wait(driver, timeout: int = DEFAULT_TIMEOUT):
    return WebDriverWait(driver, timeout)
