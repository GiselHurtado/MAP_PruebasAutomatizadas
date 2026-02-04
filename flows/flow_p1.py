# flows/flow_p1.py
"""
ORCHESTRATOR/COORDINATOR PATTERN - Orquestador del Flujo de Permiso de Trabajo

Este módulo implementa el patrón Orchestrator (no Facade) para coordinar la ejecución
completa del flujo de negocio "Permiso de Trabajo P1".

## Patrón de Diseño: Orchestrator/Coordinator

La clase FlowP1 NO es un Facade. Es un **Orchestrator** que:
- Coordina la secuencia de 11+ formularios (F1 → F1a → F7n → ... → F11)
- Gestiona cambios de sesión entre diferentes roles (operador, jefe de turno, gerencia)
- Implementa lógica de reintentos robustos para operaciones frágiles
- Maneja navegación y esperas entre transiciones de estado

## Arquitectura del Flujo

    main.py
      ↓
    FlowP1 (ORCHESTRATOR) ← Este módulo
      ↓ usa
    Page Objects (LoginPage, F1aPermisoTrabajoPage, etc.)
      ↓ usan
    elements.py (FACADE)
      ↓ delega a
    Action Classes (STRATEGIES)

## Responsabilidades

1. **Secuenciación**: Define el orden de los formularios del proceso de negocio
2. **Gestión de sesiones**: Cambia entre usuarios (operador, supervisor, gerencia)
3. **Resiliencia**: Reintentos con backoff exponencial para operaciones inestables
4. **Coordinación**: Espera notificaciones, navegación, y sincronización de tareas

## Flujo Completo del Proceso

1. Login inicial (usuario solicitante)
2. F1: Nuevo Permiso → enviar
3. F1a: Permiso de Trabajo (datos básicos) → enviar
4. F7n: Análisis de Riesgos → enviar
5. F8n: EPP Requerido → enviar
6. F9n: Condiciones de Seguridad → enviar
7. F10n: Trabajadores Autorizados → enviar
8. F10_2: Info Trabajador Autorizado → enviar
9. F10ac: Firma Trabajador Autorizado → enviar
10. F10a (1-3): Firmas de responsables (mismo usuario) → enviar
11. **Cambio de sesión → Operador**
12. F10a (4): Firma Operador → enviar
13. **Cambio de sesión → Jefe de Turno**
14. F10a (5): Firma Jefe de Turno → enviar
15. **Cambio de sesión → Gerencia**
16. F10: Firma Gerencia → enviar
17. **Cambio de sesión → Usuario inicial**
18. F11: Permiso Firmado (documento físico) → enviar

## Métodos Privados de Soporte

- `_abrir_con_reintento()`: Retry pattern para abrir tareas con backoff exponencial
- `_cambiar_sesion()`: Gestión de logout/login multi-usuario
- `_esperar_lista_tareas()`: Sincronización de navegación post-submit
- `_enviar_confirmar_robusto()`: Envío resiliente con manejo de overlays

## Uso

    from flows.flow_p1 import FlowP1

    flow = FlowP1(driver)
    flow.run(
        creds={"email": "user@example.com", "password": "pass"},
        data_f1a={...},
        data_f7n={...},
        # ... datos para cada formulario
        data_roles={
            "operador": {"email": "...", "password": "..."},
            "jefe_turno": {"email": "...", "password": "..."},
            "gerencia": {"email": "...", "password": "..."},
        }
    )
"""
from typing import Optional
import os

from pages.login_page import LoginPage
from pages.tasks_page import TasksPage
from pages.forms.f1_nuevo_permiso_page import F1NuevoPermisoPage
from pages.forms.f1a_permiso_trabajo_page import F1aPermisoTrabajoPage
from pages.forms.f7n_analisis_riesgos_page import F7nAnalisisRiesgosPage
from pages.forms.f8n_epp_requerido_page import F8nEppRequeridoPage
from pages.forms.f9n_condiciones_seguridad_page import F9nCondicionesSeguridadPage
from pages.forms.f10n_trabajadores_autorizados_page import F10nTrabajadoresAutorizadosPage
from pages.forms.f10_2_trabajador_autorizado_info_page import F10_2TrabajadorAutorizadoInfoPage
from pages.forms.f10ac_firma_permiso_page import F10acFirmaPermisoPage
from pages.forms.f10a_firma_permiso_page import F10aFirmaPermisoPage
from pages.forms.f10_firma_gerencia_page import F10FirmaGerenciaPage
from pages.forms.f11_permiso_firmado_page import F11PermisoFirmadoPage





from utils.elements import enviar_y_confirmar

# Importar clases helper refactorizadas
from utils.session_manager import SessionManager
from utils.retry_strategy import RetryStrategy
from utils.navigation_helper import NavigationHelper


class FlowP1:
    """
    Orchestrator del flujo completo de Permiso de Trabajo P1.

    Coordina 11+ formularios secuenciales con cambios de sesión entre roles.
    Ahora utiliza clases helper especializadas para separar responsabilidades:
    - SessionManager: gestión de sesiones
    - RetryStrategy: reintentos con backoff
    - NavigationHelper: navegación y esperas

    Ver docstring del módulo para detalles arquitectónicos completos.
    """
    def __init__(self, driver):
        self.driver = driver
        self.login_page = LoginPage(driver)
        self.tasks_page = TasksPage(driver)

        self.f1   = F1NuevoPermisoPage(driver)
        self.f1a  = F1aPermisoTrabajoPage(driver)
        self.f7n  = F7nAnalisisRiesgosPage(driver)
        self.f8n  = F8nEppRequeridoPage(driver)
        self.f9n  = F9nCondicionesSeguridadPage(driver)
        self.f10n = F10nTrabajadoresAutorizadosPage(driver)
        self.f10_2 = F10_2TrabajadorAutorizadoInfoPage(driver)
        self.f10ac = F10acFirmaPermisoPage(driver)
        self.f10a  = F10aFirmaPermisoPage(driver)
        self.f10_gerencia = F10FirmaGerenciaPage(driver)
        self.f11  = F11PermisoFirmadoPage(driver)

        # usa el WebDriverWait de cualquier page (todas comparten el mismo driver)
        self.wait = self.f1.wait

        # Inicializar clases helper especializadas (REFACTORIZACIÓN)
        self.session_manager = SessionManager(driver, self.wait, self.login_page)
        self.retry_strategy = RetryStrategy(driver, self.wait)
        self.navigation = NavigationHelper(driver, self.wait, self.login_page.base_url)

    def _abrir_con_reintento(self, texto: str, descripcion: Optional[str] = None,
                             intentos: int = 3, backoff=(0.8, 1.2, 2.0)):
        """Delegado a RetryStrategy para mantener compatibilidad con código existente."""
        return self.retry_strategy.retry_open_task(texto, descripcion, intentos, backoff)

    def _cambiar_sesion(self, email: str, password: str):
        """Delegado a SessionManager para mantener compatibilidad con código existente."""
        return self.session_manager.change_session(email, password)

    def _esperar_lista_tareas(self, texto_expected: str | None = None, timeout: int = 30):
        """Delegado a NavigationHelper para mantener compatibilidad con código existente."""
        return self.navigation.wait_for_tasks_list(texto_expected, timeout)

    def _esperar_que_aparezca_tarea(self, texto: str, timeout: int = 90, refresh_cada: float = 3.0):
        """Delegado a NavigationHelper para mantener compatibilidad con código existente."""
        return self.navigation.wait_for_task_to_appear(texto, timeout, refresh_cada)

    def _esperar_que_desaparezca_tarea(self, texto: str, timeout: int = 60, refresh_cada: float = 2.0):
        """Delegado a NavigationHelper para mantener compatibilidad con código existente."""
        return self.navigation.wait_for_task_to_disappear(texto, timeout, refresh_cada)

    def _enviar_y_volver_a_lista(
        self,
        texto_expected: Optional[str] = None,
        timeout: int = 30,
        max_reintentos: int = 2,
    ):
        """Delegado a NavigationHelper para mantener compatibilidad con código existente."""
        return self.navigation.send_and_return_to_list(texto_expected, timeout, max_reintentos)

    def _enviar_confirmar_robusto(self, max_reintentos: int = 4):
        """Delegado a RetryStrategy para mantener compatibilidad con código existente."""
        return self.retry_strategy.robust_send_confirm(max_reintentos)


    # =======================
    #         RUN
    # =======================
    def run(
        self,
        creds: dict,
        data_f1a: dict,
        data_f7n: Optional[dict] = None,
        data_f8n: Optional[dict] = None,
        data_f9n: Optional[dict] = None,
        data_f10n: Optional[dict] = None,
        data_f10ac: Optional[dict] = None,
        data_f10a_1: Optional[dict] = None,  # Responsable plan de emergencia
        data_f10a_2: Optional[dict] = None,  # Responsable del trabajo
        data_f10a_3: Optional[dict] = None,  # Supervisor
        data_f10a_4: Optional[dict] = None,  # Operador
        data_f10a_5: Optional[dict] = None,  # Jefe de turno
        data_f10_gerencia: Optional[dict] = None,  # Firma gerencia
        data_f11: Optional[dict] = None,  # Documento físico
        data_roles: Optional[dict] = None,
        stop_after: Optional[str] = None,
    ):
        # --- LOGIN INICIAL ---
        self.login_page.open()
        self.login_page.login(creds["email"], creds["password"])

        # --- F1 ---
        self.tasks_page.abrir_boton_nuevo_formulario()
        self.tasks_page.seleccionar_formulario_inicio_proceso()
        self.tasks_page.entrar_a_formulario_nuevo_permiso()
        self.f1.completar_y_enviar()

        # --- F1a ---
        self._abrir_con_reintento("TEBSA - F1a. Permisos de Trabajo")
        self.f1a.llenar_campos_basicos(data_f1a)
        self.f1a.seleccionar_aks_kks(data_f1a)
        self.f1a.seleccionar_empresa_e_supervisor(data_f1a)
        self.f1a.responsables_y_descripcion(data_f1a)
        self.f1a.respuestas_seguridad(data_f1a)
        enviar_y_confirmar(self.driver, self.wait)
        if stop_after == "f1a": return

        # --- F7n ---
        self._abrir_con_reintento("TEBSA - F7n. Análisis de Riesgos")
        if data_f7n:
            self.f7n.completar(data_f7n)
        enviar_y_confirmar(self.driver, self.wait)
        if stop_after == "f7n": return

        # --- F8n ---
        self._abrir_con_reintento("TEBSA - F8n. EPP Requerido")
        if data_f8n:
            self.f8n.completar(data_f8n)
        enviar_y_confirmar(self.driver, self.wait)
        if stop_after == "f8n": return

        # --- F9n ---
        self._abrir_con_reintento("TEBSA - F9n. Condiciones de Seguridad")
        self.f9n.completar(data_f9n or {"otros": "No"})
        enviar_y_confirmar(self.driver, self.wait)

        # --- F10n ---
        self._abrir_con_reintento("Trabajadores autorizados")
        self.f10n.completar_y_enviar(data_f10n)
        if stop_after == "f10n": return

        # --- F10_2 ---
        self._abrir_con_reintento("Trabajador autorizado")
        self.f10_2.completar_y_enviar(None)
        if stop_after == "f10_2": return

        # --- F10a.c ---
        self._abrir_con_reintento("TEBSA - F10a.c. Firma Permiso de Trabajo (Trabajador autorizado)")
        self.f10ac.completar_y_enviar(data_f10ac)
        if stop_after == "f10ac": return

        # --- F10a (1/2/3) con usuario actual ---
        for idx, data_fx in enumerate([data_f10a_1, data_f10a_2, data_f10a_3], start=1):
            if data_fx:
                self._abrir_con_reintento("TEBSA - F10a. Firma Permiso de Trabajo")
                print(f"➡️ F10a({idx}): Cargo = {(data_fx or {}).get('cargo')}")
                self.f10a.completar_y_enviar(data_fx)
                esperar_notificaciones_y_cargas(self.driver, self.wait, timeout=20)
                if stop_after == f"f10a_{idx}": return




        # === Cambio a OPERADOR ===
        if data_f10a_4:
            self._cambiar_sesion(
                email=data_roles["operador"]["email"],
                password=data_roles["operador"]["password"]
            )
            self._abrir_con_reintento("TEBSA - F10a. Firma Permiso de Trabajo")
            print("➡️ F10a(4) Operador: completando…")
            self.f10a.completar_y_enviar(data_f10a_4)         # firma
            enviar_y_confirmar(self.driver, self.wait)        # confirmar explícito
            esperar_notificaciones_y_cargas(self.driver, self.wait, timeout=10)
            # salir directo; no seguir buscando tareas como operador
            if stop_after in ("f10a_4", "operador"):
                return


        # === Cambio a JEFE DE TURNO ===
        if data_f10a_5:
            self._cambiar_sesion(
                email=data_roles["jefe_turno"]["email"],
                password=data_roles["jefe_turno"]["password"]
            )
            self._abrir_con_reintento("TEBSA - F10a. Firma Permiso de Trabajo")
            print("➡️ F10a(5) Jefe de turno: completando…")
            self.f10a.completar_y_enviar(data_f10a_5)
            enviar_y_confirmar(self.driver, self.wait)
            esperar_notificaciones_y_cargas(self.driver, self.wait, timeout=10)
            if stop_after in ("f10a_5", "jefe_turno"):
                return

        # === Cambio a GERENCIA: F10. Firma Gerencia ===
        if data_f10_gerencia:
            self._cambiar_sesion(
                email=data_roles["gerencia"]["email"],
                password=data_roles["gerencia"]["password"]
            )
            self._abrir_con_reintento("TEBSA - F10. Firma Gerencia")
            print("➡️ F10 (Gerencia): completando…")
            self.f10_gerencia.completar_y_enviar(data_f10_gerencia)
            enviar_y_confirmar(self.driver, self.wait)
            esperar_notificaciones_y_cargas(self.driver, self.wait, timeout=10)

            # volver al usuario inicial para cerrar con F11
            self._cambiar_sesion(email=creds["email"], password=creds["password"])
            if stop_after in ("f10_gerencia", "gerencia"):
                return


        # === F11: Permiso de Trabajo Firmado (usuario inicial) ===
        if data_f11 is not None:
            self._abrir_con_reintento("TEBSA - F11. Permiso de Trabajo Firmado (Documento físico)")
            print("➡️ F11 (Documento físico): completando…")
            self.f11.completar_y_enviar(data_f11)   # prepara la vista (sin adjunto)
            self._enviar_confirmar_robusto()        # reintentos tolerantes
            esperar_notificaciones_y_cargas(self.driver, self.wait, timeout=10)
            if stop_after == "f11":
                return

