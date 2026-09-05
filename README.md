# IES Manager

Aplicación Streamlit para la gestión del día a día del departamento, con la misma
estructura que IES Creator.

## Requisitos

- Python 3.10+
- Windows para la parte de Word/Excel

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run app.py
```

o `run_app.bat` (usa el puerto 8502 para no chocar con IES Creator).

## Funcionalidades

- Programación de aula: genera el documento Word de la programación de aula a
  partir de un Excel con los datos del grupo y las situaciones de aprendizaje.

Las pestañas se irán reorganizando y ampliando.
