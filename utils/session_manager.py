# utils/session_manager.py
"""
SessionManager - Gestión de Sesiones Multi-Usuario

Clase especializada para manejar login, logout y cambios de sesión entre diferentes
roles de usuario en los flujos de pruebas automatizadas.

Esta clase fue extraída de FlowP1._cambiar_sesion() como parte del patrón de
refactorización "Single Responsibility Principle".

Responsabilidades:
- Logout del usuario actual (múltiples estrategias)
- Login con nuevas credenciales
- Verificación de sesión activa
- Manejo de pantallas intermedias

Uso:
    from utils.session_manager import SessionManager

    session_mgr = SessionManager(driver, wait, login_page)
    session_mgr.change_session("operador@example.com", "password123")
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class SessionManager:
    """Gestiona cambios de sesión entre diferentes usuarios/roles."""

    def __init__(self, driver, wait, login_page):
        """
        Args:
            driver: WebDriver de Selenium
            wait: WebDriverWait configurado
            login_page: Instancia de LoginPage para manejar el login
        """
        self.driver = driver
        self.wait = wait
        self.login_page = login_page

    def change_session(self, email: str, password: str):
        """
        Cierra sesión del usuario actual y entra con nuevas credenciales.

        Soporta dos flujos:
        - Navbar con menú de usuario → Cerrar Sesión
        - Página /user con botón directo "Cerrar Sesión"

        Si ya estamos deslogueados, entra directo al login.

        Args:
            email: Email del nuevo usuario
            password: Contraseña del nuevo usuario
        """
        print(f"🔄 Cambiando sesión → {email}")

        # 1) Ir directo a /user (suele mostrar botón 'Cerrar Sesión')
        try:
            self.driver.get("https://apperator.ibisagroup.com/user")
        except Exception:
            pass

        # 2) Intentar cerrar sesión en /user
        cerro = self._try_logout_from_user_page()

        # 3) Si no se pudo desde /user, intentar vía navbar (menú de usuario)
        if not cerro:
            cerro = self._try_logout_from_navbar()

        # 4) Esperar a estar en login (o dar click en "Ingresar" si aparece)
        self._handle_intermediate_screen()

        # 5) Loguear con el nuevo usuario (método ya tolerante de landing)
        self.login_page.open()       # navega a base_url
        self.login_page.login(email, password)

        # 6) Confirmar que estamos dentro (navbar/tareas)
        self._verify_login_success()

        print("✅ Sesión iniciada con nuevo rol")

    def _try_logout_from_user_page(self) -> bool:
        """
        Intenta cerrar sesión desde la página /user.

        Returns:
            bool: True si se logró cerrar sesión, False en caso contrario
        """
        logout_xpaths = [
            "//button[contains(., 'Cerrar Sesión') or contains(., 'Cerrar sesión')]",
            "//*[@id='logout' or @data-testid='logout']",
            "//a[contains(., 'Cerrar Sesión') or contains(., 'Cerrar sesión')]",
        ]

        for xp in logout_xpaths:
            try:
                btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                self.driver.execute_script("arguments[0].click();", btn)
                print("✅ Clic en 'Cerrar Sesión' (vista /user)")
                return True
            except Exception:
                continue

        return False

    def _try_logout_from_navbar(self) -> bool:
        """
        Intenta cerrar sesión desde el navbar (menú de usuario).

        Returns:
            bool: True si se logró cerrar sesión, False en caso contrario
        """
        try:
            # Ir a home por si acaso
            self.driver.get("https://apperator.ibisagroup.com/")

            # Abrir menú de usuario (puede ser avatar o botón con nombre)
            menu_user_xps = [
                "//*[@id='navbar']//button[contains(@class,'user') or contains(@class,'avatar') or @aria-haspopup='menu']",
                "//*[@id='navbar']//*[contains(@class,'avatar') or contains(@class,'MuiAvatar-root')]",
                "//*[@id='navbar']//button",
            ]

            opened = False
            for xp in menu_user_xps:
                try:
                    btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                    self.driver.execute_script("arguments[0].click();", btn)
                    opened = True
                    break
                except Exception:
                    continue

            if not opened:
                return False

            # Click en opción "Cerrar Sesión" del menú
            logout_xpaths = [
                "//button[contains(., 'Cerrar Sesión') or contains(., 'Cerrar sesión')]",
                "//*[@id='logout' or @data-testid='logout']",
                "//a[contains(., 'Cerrar Sesión') or contains(., 'Cerrar sesión')]",
            ]

            for xp in logout_xpaths:
                try:
                    item = self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                    self.driver.execute_script("arguments[0].click();", item)
                    print("✅ Clic en 'Cerrar Sesión' (menú navbar)")
                    return True
                except Exception:
                    continue

        except Exception:
            pass

        return False

    def _handle_intermediate_screen(self):
        """
        Maneja pantalla intermedia con botón "Ingresar" si aparece.
        """
        try:
            from utils.elements import click_xpath
            click_xpath(self.driver, self.wait, "//*[@id='no-loged-screen']/button")
            print("ℹ️ Pantalla intermedia 'Ingresar' detectada y clickeada")
        except Exception:
            pass

    def _verify_login_success(self):
        """
        Verifica que el login fue exitoso esperando elementos de la UI autenticada.
        """
        try:
            self.wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//*[@id='task-info' or contains(@class,'tasks') or contains(@class,'task-list') or @id='navbar']"
            )))
        except Exception:
            # Fallback: esperar a que desaparezcan los campos de login
            email_xp = "//input[@type='email' or @name='email' or @autocomplete='username']"
            self.wait.until_not(EC.presence_of_element_located((By.XPATH, email_xp)))
