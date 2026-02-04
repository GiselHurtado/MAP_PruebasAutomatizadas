# pages/login_page.py
from .base_page import BasePage
from utils.elements import click_xpath
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class LoginPage(BasePage):
    base_url = "https://apperator.ibisagroup.com"

    def open(self):
        self.d.get(self.base_url)

    def login(self, email: str, password: str):
        """
        Soporta dos landings:
        1) Pantalla sin sesión con botón “Ingresar”
        2) Login directo
        """
        # Si hay botón “Ingresar”, clic
        try:
            click_xpath(self.d, self.wait, "//*[@id='no-loged-screen']/button")
        except Exception:
            pass  # puede no estar

        # Campos email y password (varios posibles atributos)
        email_xp = "//input[@type='email' or @name='email' or @autocomplete='username']"
        pass_xp  = "//input[@type='password' or @name='password' or @autocomplete='current-password']"

        email_el = self.wait.until(EC.element_to_be_clickable((By.XPATH, email_xp)))
        email_el.clear()
        email_el.send_keys(email)

        pass_el = self.wait.until(EC.element_to_be_clickable((By.XPATH, pass_xp)))
        pass_el.clear()
        pass_el.send_keys(password)

        # Botón ingresar
        login_btn_xps = [
            "//button[@type='submit']",
            "//button[contains(., 'Ingresar') or contains(., 'Login')]",
        ]
        for xp in login_btn_xps:
            try:
                btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                self.d.execute_script("arguments[0].click();", btn)
                break
            except Exception:
                continue

        # Espera a que desaparezcan loaders y exista algún contenedor de tareas/home
        try:
            self.wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//*[@id='task-info' or contains(@class,'tasks') or contains(@class,'task-list') or @id='navbar']"
            )))
        except Exception:
            # como mínimo, que no estemos en la pantalla de login ya
            self.wait.until_not(EC.presence_of_element_located((By.XPATH, email_xp)))
