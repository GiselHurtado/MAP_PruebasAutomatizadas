# MAP_PruebasAutomatizadas

Este proyecto contiene pruebas automatizadas desarrolladas con **Selenium** y **Python** para el sistema MAP.


## Requisitos Previos

*   **Python 3.8+**
*   **Google Chrome** instalado.
*   **Git** (opcional, para clonar el repositorio).

## Instalación

1.  **Clonar el repositorio** (si aún no lo tienes):
    ```bash
    git clone https://github.com/GiselHurtado/MAP_PruebasAutomatizadas.git
    cd MAP_PruebasAutomatizadas
    ```

2.  **Crear un entorno virtual** (recomendado):
    ```bash
    # En Windows
    python -m venv venv
    .\venv\Scripts\activate

    # En Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instalar las dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuración

1.  **Variables de Entorno**:
    Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`.
    ```bash
    cp .env.example .env
    ```
    Edita el archivo `.env` con tus credenciales:
    ```ini
    APP_EMAIL=usuario@tebsa.com
    APP_PASSWORD=TuPasswordAqui
    ```

2.  **Datos de Prueba**:
    Los datos utilizados para las pruebas se encuentran en la carpeta `data/`.
    *   Ejemplo: `data/p1_permiso_trabajo.yaml` contiene la configuración para el flujo de permisos de trabajo.

## Ejecución

### Ejecutar el Flujo P1 (Script Principal)
Para correr el flujo principal definido en `main.py`:

```bash
python main.py
```
Este script leerá las credenciales del `.env` y los datos del archivo YAML para ejecutar el flujo `FlowP1`.

### Ejecutar Tests con Pytest
El proyecto está configurado para usar `pytest`. Puedes ejecutar todas las pruebas con:

```bash
pytest
```

Para ver la salida detallada (logs y prints):
```bash
pytest -s
```

Para generar reportes (si se configura pytest-html u otro plugin):
```bash
pytest --html=reports/report.html
```

## Estructura del Proyecto

*   **`main.py`**: Punto de entrada para ejecutar flujos manualmente.
*   **`pages/`**: Contiene las clases que representan las páginas web (Page Object Model).
*   **`flows/`**: Lógica de negocio que orquesta interacciones entre múltiples páginas.
*   **`utils/`**: Utilidades generales (configuración del driver, helpers, etc.).
*   **`data/`**: Archivos YAML con datos de prueba.
*   **`tests/`**: Tests unitarios o de integración ejecutables con pytest.
*   **`.env`**: Archivo de configuración de variables secretas.
