from .base_page import BasePage
from utils.elements import click_xpath

class TasksPage(BasePage):

    def abrir_boton_nuevo_formulario(self):
        click_xpath(self.d, self.wait, "//*[@id='tasks']/button")
        print("✅ Botón verde para nuevo formulario")

    def seleccionar_formulario_inicio_proceso(self):
        # TEBSA - F1. Nuevo permiso de trabajo
        click_xpath(self.d, self.wait, "//div[@class='form' and contains(text(), 'TEBSA - F1. Nuevo permiso de trabajo')]")
        print("✅ Selecciona el formulario que inicia el proceso")

    def entrar_a_formulario_nuevo_permiso(self):
        click_xpath(self.d, self.wait, "//div[@class='task-item']//span[contains(text(), 'TEBSA - F1. Nuevo permiso de trabajo')]")
        print("✅ Entra al formulario Nuevo permiso")
