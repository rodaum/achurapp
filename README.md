# 🔥 Achurapp

App web para organizar las compras de un asado. El organizador crea el asado y comparte un link; cada invitado cuenta qué quiere comer; la app junta las respuestas y arma la lista de compras, con cantidades calculadas para que **sobre en vez de que falte**.

## Cómo funciona

| Link                           | Pantalla                                                                    |
| ------------------------------ | --------------------------------------------------------------------------- |
| sin parámetros                 | **Crear asado**: devuelve el link para invitados y el del organizador.      |
| `?asado=<slug>`                | **Formulario del invitado**: cortes, achuras, acompañamientos y apetito.    |
| `?asado=<slug>&admin=<clave>`  | **Vista del organizador**: respuestas y lista de compras para WhatsApp.     |

Las cantidades se calculan por persona (400 g de carne por adulto, ajustado por apetito y si es chico/a), se les suma un 15 % extra y se redondean siempre hacia arriba. Las reglas completas están en [SPEC.md](SPEC.md) y las constantes en [config.py](config.py).

## Estructura

```
app.py         pantallas y ruteo por URL (Streamlit)
config.py      opciones del formulario y constantes de cálculo
calculo.py     lógica de cantidades (funciones puras)
db.py          acceso a Postgres (Neon)
tests/         tests del cálculo (pytest)
```

## Correrla local

Requiere Python 3.11 o superior (también anda en 3.10).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # y completar la URL (ver abajo)
streamlit run app.py
```

La app abre en http://localhost:8501. Para correr los tests:

```bash
pytest
```

## Configurar Neon (base de datos)

1. Crear una cuenta en [neon.tech](https://neon.tech) y un proyecto (el plan gratis alcanza).
2. En el Dashboard del proyecto, tocar **Connect** y copiar la cadena de conexión (`postgresql://...`).
3. Pegarla en `.streamlit/secrets.toml`:

   ```toml
   [connections.sql]
   url = "postgresql://usuario:password@host.neon.tech/basededatos?sslmode=require"
   ```

La app crea las tablas sola la primera vez que se conecta. `secrets.toml` está en `.gitignore`: **nunca lo subas al repo**.

## Deploy en Streamlit Community Cloud

1. Subir el repo a GitHub (público).
2. Entrar a [share.streamlit.io](https://share.streamlit.io) con la cuenta de GitHub y tocar **Create app** → **Deploy a public app from GitHub**.
3. Elegir el repo, la rama `main` y el archivo principal `app.py`.
4. En **Advanced settings**:
   - **Python version**: 3.12 (o la más nueva que ofrezca).
   - **Secrets**: pegar el mismo contenido que `.streamlit/secrets.toml` (la sección `[connections.sql]` con la URL real).
5. Tocar **Deploy**. Los secrets se pueden cambiar después desde la app en el panel: **⋮ → Settings → Secrets**.

## ⚠️ Antes de una demo

Streamlit Community Cloud **duerme la app tras 12 h sin visitas**, y Neon **suspende la base** cuando no se usa. Abrí la app unos minutos antes para despertarla: la primera carga puede tardar y hasta pedir que toques un botón para reactivarla.
