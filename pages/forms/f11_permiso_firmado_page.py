# pages/forms/f11_permiso_firmado_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class F11PermisoFirmadoPage:
    """
    TEBSA – F11. Permiso de Trabajo Firmado (Documento físico)
    Campo de foto: opcional. Preparamos la UI para que el botón Enviar sea clickeable.
    El click de Enviar/Confirmar lo hace el flow (_enviar_confirmar_robusto).
    """

    def __init__(self, driver, timeout: int = 20):
        self.d = driver
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.timeout = timeout

    def completar(self, data: dict):
        """
        No subimos archivo (servidor inestable / campo opcional).
        Cerramos overlays, quitamos foco y desplazamos al pie.
        """
        # Si más adelante quieres reactivar la subida, descomenta:
        # ruta = (data or {}).get("archivo")
        # if ruta:
        #     try:
        #         self.subir_foto_F11(ruta)
        #     except Exception as e:
        #         print(f"⚠️ F11: subida opcional falló: {e}")

        try:
            self.d.execute_script("""
                if (document.activeElement && document.activeElement.blur) { document.activeElement.blur(); }
                const sels = ['.MuiBackdrop-root','.MuiModal-root','.MuiPopover-root','.MuiMenu-root',
                              '[role="dialog"]','[role="menu"]','.popup','.dialog'];
                document.querySelectorAll(sels.join(',')).forEach(el => { try{el.style.display='none'}catch(_){ } });
                window.dispatchEvent(new Event('resize'));
            """)
        except Exception:
            pass

        try:
            self.d.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        except Exception:
            pass

        print("ℹ️ F11: omitimos la carga de foto (campo opcional).")

    def completar_y_enviar(self, data: dict):
        """
        Mantiene el contrato del flow: prepara el formulario y lo deja listo.
        """
        self.completar(data)
        print("🟢 F11 listo para enviar (sin adjunto).")

    # Placeholder para futura reactivación (opcional)
    def subir_foto_F11(self, ruta_archivo: str):
        print(f"ℹ️ F11: placeholder subir_foto_F11('{ruta_archivo}') (actualmente desactivado)")
