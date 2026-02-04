from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.common.keys import Keys 
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException 
import time
from datetime import datetime

# --- Funciones reutilizables ---
def click_xpath(driver, wait, xpath):
    elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    elem.click()
    return elem

def escribir_xpath(driver, wait, xpath, texto):
    elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    elem.clear()
    elem.send_keys(texto)
    return elem

def enviar_y_confirmar(driver, wait):
    """
    Envía un formulario (botón verde) y luego confirma (botón azul).
    """
    # --- Enviar ---
    botones = wait.until(
        EC.presence_of_all_elements_located((By.XPATH, "//button[contains(@class,'btn-green')]"))
    )
    if not botones:
        raise Exception("❌ No se encontró ningún botón verde en el formulario")
    boton_enviar = botones[-1]
    driver.execute_script("arguments[0].scrollIntoView(true);", boton_enviar)
    boton_enviar.click()
    print("✅ Formulario enviado")

    # --- Confirmar ---
    try:
        boton_confirmar = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'btn-blue')]"))
        )
        boton_confirmar.click()
        print("✅ Confirmación enviada")
    except TimeoutException:
        print("⚠️ No se encontró botón azul de confirmación")

def abrir_siguiente_formulario(driver, wait, xpath_tarea, descripcion="Formulario"):
    """
    Espera notificación, luego hace click en el formulario siguiente.
    """
    # esperar notificación
    esperar_notificacion(driver)
    print("🔔 Notificación cerrada")

    # click en el formulario
    elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_tarea)))
    driver.execute_script("arguments[0].click();", elem)
    print(f"✅ Se abrió {descripcion}")

def campo_texto(driver, wait, etiqueta, texto):
    """ Busca un campo de texto por su label y escribe el valor dado. """
    campo = wait.until(EC.element_to_be_clickable((
        By.XPATH, f"//label[contains(normalize-space(.), '{etiqueta}')]/following::input[1]"
    )))
    campo.clear()
    campo.send_keys(texto)
    return campo

def esperar_notificacion(driver, timeout=20):
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "push-notification-container")))
    wait.until_not(EC.presence_of_element_located((By.CLASS_NAME, "pushing")))

def seleccion_simple(driver, wait, etiqueta, texto, opcion=1):
    cont = wait.until(EC.presence_of_element_located((
        By.XPATH, f"//label[contains(normalize-space(.), \"{etiqueta}\")]/ancestor::div[contains(@class,'MuiFormControl-root')][1]"
    )))
    inp = cont.find_element(By.CSS_SELECTOR, "input[role='combobox'], input")
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[role='combobox'], input")))
    inp.clear()
    inp.send_keys(texto)
    opcion_css = f"ul li:nth-child({opcion})"
    opcion_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, opcion_css)))
    opcion_elem.click()

def escribir_fecha(driver, wait, etiqueta, fecha):
    campo = wait.until(EC.element_to_be_clickable((
        By.XPATH, f"//label[contains(normalize-space(.), '{etiqueta}')]/following::input[1]"
    )))
    campo.click()
    campo.send_keys(Keys.CONTROL, "a")
    campo.send_keys(Keys.DELETE)
    campo.send_keys(fecha)
    campo.send_keys(Keys.ENTER)
    return campo

def campo_endpoint(
    driver, wait,
    xpath_boton_lupa,
    label_dropdown, opcion_texto,
    label_input=None, valor_input=None,  # Opcionales: si se pasan, rellena input
    opcion=1,
    delay=2
):
    """
    Flujo genérico para campos tipo endpoint:
      1) (Opcional) Si label_input y valor_input existen → rellenar input
      2) Click en la lupa usando xpath_boton_lupa
      3) Esperar delay segundos
      4) Usar seleccion_simple para elegir opcion_texto en label_dropdown
    """

    # 1) rellenar input si corresponde
    if label_input and valor_input:
        try:
            input_xpath = f"//label[contains(normalize-space(.), '{label_input}')]/following::input[1]"
            campo = wait.until(EC.element_to_be_clickable((By.XPATH, input_xpath)))
            campo.clear()
            campo.send_keys(valor_input)
            print(f"✍️ Input '{label_input}' llenado con '{valor_input}'")
            time.sleep(0.3)
        except TimeoutException:
            print(f"⚠️ No se encontró input para {label_input}")

    # 2) click en lupa usando xpath recibido
    try:
        boton_lupa = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_boton_lupa)))
        driver.execute_script("arguments[0].click();", boton_lupa)
        print(f"🔍 Click en lupa ({xpath_boton_lupa})")
    except TimeoutException:
        print(f"⚠️ No se encontró lupa en {xpath_boton_lupa}")
        return

    # 3) esperar
    time.sleep(delay)

    # 4) selección en dropdown
    seleccion_simple(driver, wait, label_dropdown, opcion_texto, opcion=opcion)
    print(f"✅ Seleccionado '{opcion_texto}' en {label_dropdown}")

# --- Configuración del navegador ---
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
prefs = { "profile.default_content_setting_values.notifications": 2 }
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

# --- LOGIN ---
driver.get("https://apperator.ibisagroup.com/")
click_xpath(driver, wait, "//*[@id='no-loged-screen']/button")
escribir_xpath(driver, wait, "//input[@type='email']", "usuario@tebsa.com")
enter_pass = escribir_xpath(driver, wait, "//input[@type='password']", "Tebsa2023!")
enter_pass.send_keys(Keys.ENTER)
print("✅ Login exitoso")
time.sleep(5)


# --- Abrir el formulario inicial ---
click_xpath(driver, wait, "//*[@id='tasks']/button")
print("✅ Botón verde para nuevo formulario")

click_xpath(driver, wait, "//div[@class='form' and contains(text(), 'TEBSA - F1. Nuevo permiso de trabajo')]")
print("✅ Selecciona el formulario que inicia el proceso")

click_xpath(driver, wait, "//div[@class='task-item']//span[contains(text(), 'TEBSA - F1. Nuevo permiso de trabajo')]")
print("✅ Entra al formulario Nuevo permiso")

enviar_y_confirmar(driver, wait)

abrir_siguiente_formulario(
    driver, wait,
    '//*[@id="task-info"]/span[1]',
    descripcion="TEBSA - F1a. Permisos de Trabajo"
)

# 1.
campo_texto(driver, wait, "Orden de trabajo", "Tebsa2025 - 001")
print("✅ Campo Orden de trabajo escrito correctamente")

# 2.
seleccion_simple(driver, wait, "Identificación permiso", "ABB", opcion=1)
print("✅ Identificacion de permiso")

# 3.
escribir_fecha(driver, wait, "Vigente desde", "27/02/2025 10:25 AM")
print("✅ vigente desde")

# 4.
escribir_fecha(driver, wait, "Vigente hasta", "28/03/2025 05:30 PM")
print("✅ vigente hasta")

# 5.
seleccion_simple(driver, wait, "Lugar de trabajo", "Almacén", opcion=1)

# 6.
campo_endpoint(
    driver, wait,
    xpath_boton_lupa="//*[@id='auto-fields']/div[1]/div[6]/button",
    label_input="kks", valor_input="24max",
    label_dropdown="AKS/KKS",
    opcion_texto="SIST. SUM. ACEITE MANDO - SISTEMA SUM. ACEITE DE MANDO (No usar) - 24MAX11"
)

# 7.
campo_endpoint(
    driver, wait,
    xpath_boton_lupa="//*[@id='auto-fields']/div[1]/div[7]/button",
    label_dropdown="Empresa que ejecuta el trabajo",
    opcion_texto="Metales",
    opcion=1
)

# 8. 
seleccion_simple(driver, wait, "Supervisor TEBSA", "ALBERTO ESCAÑO", opcion=1)
print("✅ supervisor aleberto")

# 9. Responsable del trabajo
campo_texto(driver, wait, "Responsable del trabajo", "CESAR SIERRA")
print("✅ Campo Responsable del trabajo escrito correctamente")

# 10. Descripcion del trabajo
campo_texto(driver, wait, "Descripcion del trabajo", "revision de chimeneas - prueba 1")
print("✅ Campo Descripcion del trabajoo escrito correctamente")

# 11. 
seleccion_simple(driver, wait, "Es un area clasificada?", "Si")
print("✅ Campo Es un area clasificada? escrito correctamente")

# 12. 
seleccion_simple(driver, wait, "Area Clasificada", "Estacion Reductora")
print("✅ Campo Area Clasificada escrito correctamente")

# 13. 
seleccion_simple(driver, wait, "Es un area restringida? ", "No")
print("✅ Campo Es un area restringida?  escrito correctamente")

# 14. 
seleccion_simple(driver, wait, "Requiere LOTO? ", "No")
print("✅ Campo Requiere LOTO? escrito correctamente")

# 15. 
seleccion_simple(driver, wait, "Requiere espacio confinado?", "No")
print("✅ Campo Requiere espacio confinado? escrito correctamente")

# 16. 
seleccion_simple(driver, wait, "Requiere trabajo seguro en altura? ", "Si")
print("✅ Campo Requiere trabajo seguro en altura? escrito correctamente")

# 17. 
seleccion_simple(driver, wait, "Requiere trabajo en caliente?", "No")
print("✅ Campo Requiere trabajo en caliente? correctamente")

# 18. 
seleccion_simple(driver, wait, "Requiere trabajo con tension?", "No")
print("✅ Campo Requiere trabajo con tension?  correctamente")

# 19. 
seleccion_simple(driver, wait, "Requiere autorizacion de Gerencia de planta?", "si")
print("✅ Campo Requiere autorizacion de Gerencia de planta? correctamente")

# 19. 
seleccion_simple(driver, wait, "Motivo", "PARADA UNIDAD")
print("✅ Campo Motivo correctamente")

#Final del segundo formulario


enviar_y_confirmar(driver, wait)

abrir_siguiente_formulario(
    driver, wait,
    '//*[@id="task-info"]/span[2]',
    descripcion="TEBSA - F7n. Análisis de Riesgos"
)




