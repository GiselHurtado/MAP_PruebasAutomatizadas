from ..base_page import BasePage
from utils.elements import (
    campo_texto_por_label,
    seleccion_simple,
    escribir_fecha,
    campo_endpoint,
)

class F1aPermisoTrabajoPage(BasePage):
    """TEBSA - F1a. Permisos de Trabajo"""

    def llenar_campos_basicos(self, data: dict):
        # 1. Orden de trabajo *
        campo_texto_por_label(self.d, self.wait, "Orden de trabajo", data["orden_trabajo"])
        # 2. Identificación permiso
        seleccion_simple(self.d, self.wait, "Identificación permiso", data["identificacion_permiso"], opcion=1)
        # 3. Vigente desde *
        escribir_fecha(self.d, self.wait, "Vigente desde", data["vigente_desde"])
        # 4. Vigente hasta *
        escribir_fecha(self.d, self.wait, "Vigente hasta", data["vigente_hasta"])
        # 5. Lugar de trabajo
        seleccion_simple(self.d, self.wait, "Lugar de trabajo", data["lugar_trabajo"], opcion=1)

    def seleccionar_aks_kks(self, data: dict):
        # 6. AKS/KKS (endpoint con input kks)
        campo_endpoint(
            self.d, self.wait,
            xpath_boton_lupa="//*[@id='auto-fields']/div[1]/div[6]/button",
            label_input="kks", valor_input=data["kks_valor"],
            label_dropdown="AKS/KKS",
            opcion_texto=data["aks_kks_opcion"]
        )

    def seleccionar_empresa_e_supervisor(self, data: dict):
        # 7. Empresa que ejecuta el trabajo
        campo_endpoint(
            self.d, self.wait,
            xpath_boton_lupa="//*[@id='auto-fields']/div[1]/div[7]/button",
            label_dropdown="Empresa que ejecuta el trabajo",
            opcion_texto=data["empresa_ejecuta"], opcion=1
        )
        # 8. Supervisor TEBSA *
        seleccion_simple(self.d, self.wait, "Supervisor TEBSA", data["supervisor_tebsa"], opcion=1)

    def responsables_y_descripcion(self, data: dict):
        # 9. Responsable del trabajo *
        campo_texto_por_label(self.d, self.wait, "Responsable del trabajo", data["responsable_trabajo"])
        # 10. Descripcion del trabajo *
        campo_texto_por_label(self.d, self.wait, "Descripcion del trabajo", data["descripcion_trabajo"])

    def respuestas_seguridad(self, data: dict):
        # 11..19 flags varios
        seleccion_simple(self.d, self.wait, "Es un area clasificada?", data["area_clasificada"])
        if data["area_clasificada"] == "Si":
            seleccion_simple(self.d, self.wait, "Area Clasificada", data["tipo_area_clasificada"])

        seleccion_simple(self.d, self.wait, "Es un area restringida? ", data["area_restringida"])
        seleccion_simple(self.d, self.wait, "Requiere LOTO? ", data["requiere_loto"])
        seleccion_simple(self.d, self.wait, "Requiere espacio confinado?", data["espacio_confinado"])
        seleccion_simple(self.d, self.wait, "Requiere trabajo seguro en altura? ", data["trabajo_altura"])
        seleccion_simple(self.d, self.wait, "Requiere trabajo en caliente?", data["trabajo_caliente"])
        seleccion_simple(self.d, self.wait, "Requiere trabajo con tension?", data["trabajo_tension"])
        seleccion_simple(self.d, self.wait, "Requiere autorizacion de Gerencia de planta?", data["autoriza_gerencia"])
        # 19. Motivo
        seleccion_simple(self.d, self.wait, "Motivo", data["motivo"])

