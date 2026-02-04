# utils/actions/common_actions.py
from selenium.webdriver.common.by import By

class CommonActions:
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def click_xpath(self, xpath: str, timeout: int = 15):
        raise NotImplementedError

    def escribir_xpath(self, xpath: str, texto: str):
        raise NotImplementedError

    def esperar_notificaciones_y_cargas(self, timeout: int = 20):
        raise NotImplementedError
