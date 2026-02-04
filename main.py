import os
import yaml
from utils.browser import build_driver
from flows.flow_p1 import FlowP1

def read_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    # Lee .env si quieres (opcional)
    email = os.getenv("APP_EMAIL", "usuario@tebsa.com")
    password = os.getenv("APP_PASSWORD", "Tebsa2023!")

    data = read_yaml("data/p1_permiso_trabajo.yaml")
    data_f1a = data["f1a"]
    data_f7n = data.get("f7n", {})

    driver = build_driver(headless=False)
    try:
        FlowP1(driver).run({"email": email, "password": password}, data_f1a, data_f7n)
    finally:
        driver.quit()
