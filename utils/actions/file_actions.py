# utils/actions/file_actions.py
"""
STRATEGY PATTERN - Estrategia para Subida de Archivos

Esta clase implementa el patrón Strategy para manejar la subida de archivos:
- Inputs dinámicos (input[type=file] inyectado tras click)
- Archivos de foto/imagen
- Documentos PDF

Forma parte del conjunto de estrategias especializadas en utils/actions/ que
son utilizadas a través del Facade Pattern en utils/elements.py.

Uso desde Page Objects (a través de la facade):
    from utils.elements import subir_archivo
    subir_archivo(driver, wait, "Seleccionar una foto", "C:/ruta/imagen.jpg")
"""
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from utils.actions.base_action import BaseAction

class FileActions(BaseAction):
    """Hereda de BaseAction para aprovechar métodos helper comunes."""
    pass  # __init__ heredado de BaseAction

    def subir_archivo(self, etiqueta_boton: str, ruta_archivo: str, timeout: int = 30):
        """Sube un archivo usando un botón que dispara un <input type='file'> dinámico.
        Mantiene la lógica original y los waits/reintentos.
        """
        driver = self.driver
        wait = self.wait

        # 1) Click en el botón (por texto visible)
        boton_xpath = f"//button[contains(normalize-space(.), '{etiqueta_boton}')]"
        boton = wait.until(EC.element_to_be_clickable((By.XPATH, boton_xpath)))
        try:
            boton.click()
        except Exception:
            driver.execute_script("arguments[0].click();", boton)

        # 2) Esperar a que el input file aparezca (inyectado en cualquier parte del DOM)
        fin = time.time() + timeout
        input_file = None
        while time.time() < fin:
            inputs = driver.find_elements(By.XPATH, "//input[@type='file' and not(@disabled)]")
            if inputs:
                # Tomamos el último por si el framework creó uno nuevo al hacer click
                input_file = inputs[-1]
                break
            time.sleep(0.15)
        if not input_file:
            raise TimeoutException("No apareció ningún <input type='file'> tras pulsar el botón.")

        # 3) Asegurar que se pueda escribir y cargar el archivo
        try:
            input_file.send_keys(ruta_archivo)
        except ElementNotInteractableException:
            # fuerza visibilidad si el framework lo dejó oculto
            driver.execute_script("""
                arguments[0].style.display='block';
                arguments[0].style.visibility='visible';
                arguments[0].style.opacity=1;
            """, input_file)
            input_file.send_keys(ruta_archivo)

        # 4) Verificación: el widget suele actualizar el texto de “fotos seleccionadas”
        try:
            # busca el bloque de estado cercano al botón (si existe)
            cont_estado = driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'selected-photos') or contains(normalize-space(.),'fotos seleccionadas')]"
            )
            if cont_estado:
                wait.until_not(
                    lambda d: "No hay fotos seleccionadas" in cont_estado[0].text
                )
        except Exception:
            # no pasa nada; algunas UIs no muestran ese texto, y la carga ya fue enviada
            pass

        print(f"✅ Archivo '{ruta_archivo}' cargado en '{etiqueta_boton}'")

        # --- segunda estrategia: buscar input cercano al botón/label (fallbacks) ---
        boton_xpath = " | ".join([
            f"//button[contains(normalize-space(.), '{etiqueta_boton}')]",
            f"//button[.//span[contains(normalize-space(.), '{etiqueta_boton}')]]",
            f"//label[contains(normalize-space(.), '{etiqueta_boton}')]",
        ])
        boton = wait.until(EC.presence_of_element_located((By.XPATH, boton_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", boton)

        # 2) Definir contenedores candidatos alrededor del botón
        candidatos_contenedor = []
        try:
            candidatos_contenedor.append(
                boton.find_element(By.XPATH, "./ancestor::*[contains(@class,'photo-field')][1]")
            )
        except Exception:
            pass
        try:
            candidatos_contenedor.append(
                boton.find_element(By.XPATH, "./ancestor::*[contains(@class,'MuiCard') or contains(@class,'card')][1]")
            )
        except Exception:
            pass
        try:
            candidatos_contenedor.append(
                boton.find_element(By.XPATH, "./ancestor::*[self::div or self::section][1]")
            )
        except Exception:
            pass

        candidatos_contenedor = [c for i, c in enumerate(candidatos_contenedor) if c and c not in candidatos_contenedor[:i]]

        xpaths_input_rel = [
            ".//input[@type='file']",
            ".//input[@type='file' and contains(@accept,'image')]",
            ".//input[contains(@type,'file')]",
            "following::input[@type='file'][1]",
        ]

        input_file = None
        for cont in candidatos_contenedor:
            for xp in xpaths_input_rel:
                try:
                    input_file = cont.find_element(By.XPATH, xp)
                    break
                except Exception:
                    continue
            if input_file:
                break

        if not input_file:
            candidatos_globales = driver.find_elements(By.XPATH, "//input[@type='file']")
            if candidatos_globales:
                boton_rect = driver.execute_script("return arguments[0].getBoundingClientRect();", boton)
                def dist_y(el):
                    r = driver.execute_script("return arguments[0].getBoundingClientRect();", el)
                    return abs((r.get('top', 0) or 0) - (boton_rect.get('top', 0) or 0))
                candidatos_globales.sort(key=dist_y)
                input_file = candidatos_globales[0]

        if not input_file:
            raise Exception(f"No se encontró ningún <input type='file'> asociado a '{etiqueta_boton}'")

        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_file)
        except Exception:
            pass
        try:
            driver.execute_script("arguments[0].style.display='block'; arguments[0].removeAttribute('hidden');", input_file)
        except Exception:
            pass

        input_file.send_keys(ruta_archivo)
        print(f"✅ Archivo '{ruta_archivo}' cargado en '{etiqueta_boton}'")

    def _buscar_input_file_en_dom(self):
        """Busca un input[type=file] habilitado en todo el DOM."""
        driver = self.driver
        xps = [
            "//div[contains(@class,'photo-field')]//input[@type='file' and not(@disabled)]",
            "//form//input[@type='file' and not(@disabled)]",
            "//input[@type='file' and not(@disabled)]",
        ]
        for xp in xps:
            els = driver.find_elements(By.XPATH, xp)
            for el in els:
                try:
                    disabled = el.get_attribute("disabled")
                    if not disabled:
                        return el
                except Exception:
                    continue
        return None

    def subir_archivo_por_boton(self, etiqueta_boton: str, ruta_archivo: str, timeout: int = 6):
        """Hace click en el botón (p.e. 'Seleccionar una foto') y sube el archivo
        tratando de localizar el <input type='file'> que el front inserta dinámicamente."""
        driver = self.driver
        wait = self.wait

        boton_xpath = f"//button[contains(normalize-space(.), '{etiqueta_boton}')]"
        boton = wait.until(EC.element_to_be_clickable((By.XPATH, boton_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", boton)
        try:
            boton.click()
        except Exception:
            driver.execute_script("arguments[0].click();", boton)

        fin = time.time() + timeout
        input_file = None
        while time.time() < fin and input_file is None:
            time.sleep(0.25)
            input_file = self._buscar_input_file_en_dom()

        if input_file is None:
            raise Exception(f"No se encontró ningún <input type='file'> asociado a '{etiqueta_boton}'")

        try:
            driver.execute_script("arguments[0].style.display='block'; arguments[0].style.opacity=1;", input_file)
        except Exception:
            pass

        input_file.send_keys(ruta_archivo)
        print(f"✅ Archivo '{ruta_archivo}' cargado en '{etiqueta_boton}'")
