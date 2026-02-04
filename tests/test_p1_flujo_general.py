# tests/test_p1_flujo_general.py (nuevo caso o reemplazo)
import os
import pytest
import yaml

from utils.browser import build_driver
from flows.flow_p1 import FlowP1

def read_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@pytest.mark.p1
def test_p1_hasta_f11():
    creds = {"email": os.getenv("APP_EMAIL"), "password": os.getenv("APP_PASSWORD")}
    data  = read_yaml("data/p1_permiso_trabajo.yaml")

    driver = build_driver(headless=False)
    try:
        flow = FlowP1(driver)
        flow.run(
            creds=creds,
            data_f1a   = data["f1a"],
            data_f7n   = data["f7n"],
            data_f8n   = data["f8n"],
            data_f9n   = data.get("f9n", {"otros":"No"}),
            data_f10n  = data["f10n"],               # Trabajadores autorizados
            data_f10ac = data.get("f10ac", {"etiqueta_firma": "Firma"}),
            data_f10a_1 = data["f10a_1"],            # Responsable plan emergencia
            data_f10a_2 = data["f10a_2"],            # Resp. trabajo 
            data_f10a_3 = data["f10a_3"],            # Supervisor o Resp. trabajo 
            data_f10a_4 = data["f10a_4"],            # Operador
            data_f10a_5 = data["f10a_5"],            # Jefe de turno
            data_f10_gerencia = data["f10_gerencia"],# Gerencia
            data_f11  = data.get("f11", {}),         # cierre
            data_roles = data["roles"],              # credenciales por rol
            stop_after="f11",                        # dejamos que llegue al final
        )
    finally:
        driver.quit()
