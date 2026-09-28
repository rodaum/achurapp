# Proyecto: "Asado" — app para organizar las compras de un asado

## Contexto

Quiero construir una app web chica para organizar un asado. El organizador crea un asado y comparte un link; cada invitado completa sus preferencias; la app junta todas las respuestas y genera la lista de compras con cantidades calculadas para que sobre en vez de que falte.

Es un proyecto personal para una exposición breve. Tiene que ser **simple, legible y fácil de explicar**. Prioridades, en orden: que funcione, que el código se entienda, que sea corto.

## Reglas de trabajo

- **Trabajá por etapas (2 a 6, abajo) y detenete al terminar cada una.** Al cerrar una etapa, mostrame:
  1. qué archivos creaste o cambiaste y por qué, en pocas líneas;
  2. **cómo lo verifico yo a mano** (comandos a correr y qué debería ver). No me des scripts de verificación armados: quiero probarlo yo.
     No avances a la siguiente etapa hasta que te lo diga.
- La interfaz está **en español (Argentina)**.
- **La app no usa IA ni APIs externas** además de la base de datos.
- **No agregues dependencias** fuera de las listadas sin preguntarme antes.
- **Los secretos nunca van al repo.** La cadena de conexión va en `.streamlit/secrets.toml` (en `.gitignore`); en el repo solo existe `.streamlit/secrets.toml.example` con valores ficticios. El repo va a ser público.
- Nada de autenticación compleja, frameworks extra ni sobreingeniería. Si dudás entre dos formas, elegí la más simple y mencionámelo.
- Tamaño objetivo: unas 300 líneas de Python en total (sin contar tests).

## Stack

- Python 3.11+
- Streamlit (UI y ruteo por parámetros de URL con `st.query_params`)
- Neon (Postgres) vía `st.connection("sql")` con SQLAlchemy + `psycopg2-binary`
- pytest para los tests de la lógica de cálculo
- Deploy: GitHub (repo público) + Streamlit Community Cloud

`requirements.txt`: `streamlit`, `sqlalchemy`, `psycopg2-binary`, `pytest`.

## Estructura de archivos

Todo va en la **raíz del repo** (sin subcarpeta `asado/`):

```
./
├── app.py            # ruteo y pantallas de Streamlit
├── config.py         # opciones del formulario y constantes de cálculo
├── calculo.py        # lógica de cantidades (funciones puras, sin Streamlit ni DB)
├── db.py             # acceso a datos
├── tests/
│   └── test_calculo.py
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example
└── README.md
```

`calculo.py` no debe importar nada de Streamlit ni de la base: recibe datos, devuelve datos.

## Pantallas (ruteo por URL)

| URL                           | Pantalla                                                                                                                      |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| sin parámetros                | **Crear asado**: nombre y fecha (opcional). Al crear, muestra el link para invitados y el link del organizador (con aviso de guardarlo). |
| `?asado=<slug>`               | **Formulario del invitado**                                                                                                   |
| `?asado=<slug>&admin=<clave>` | **Vista del organizador**                                                                                                     |

- `slug`: derivado del nombre del asado + sufijo aleatorio corto (ej. `cumple-juan-x7k2`). Se quitan tildes y ñ con `unicodedata` (biblioteca estándar).
- Links absolutos: se arman con `st.context.url` si la versión de Streamlit lo trae; si no, se muestra solo la parte `?asado=...`.
- `clave`: token aleatorio (`secrets.token_urlsafe(8)`). No es seguridad real; alcanza para que un invitado no vea la vista del organizador por accidente.
- Si el `slug` no existe o la clave es incorrecta, mostrar un mensaje claro.

### Formulario del invitado

- Nombre (obligatorio). Texto de ayuda: "Si alguien más tiene tu nombre, agregá tu apellido".
- ¿Es chico/a? (casilla)
- ¿Es vegetariano/a? (casilla, **fuera del `st.form`** para que al tildarla se oculten al instante las secciones de carnes y achuras).
- Apetito: poco / normal / mucho (por defecto: normal).
- Preferencias por categoría, con casillas múltiples (ver `config.py` abajo).
- Validación, con mensaje claro:
  - si no es vegetariano, tiene que elegir al menos un corte de carne (vaca, cerdo o pollo);
  - si es vegetariano, tiene que elegir al menos un acompañamiento.
- Si es vegetariano, las elecciones de carne y achuras se descartan al guardar.
- Si alguien envía de nuevo con el mismo nombre en el mismo asado, **se actualiza su respuesta** (no se duplica). Los nombres se comparan **sin espacios al borde y sin distinguir mayúsculas/minúsculas** ("Juan" = " juan "); se muestra el nombre tal como se escribió en el último envío.
- Confirmación al guardar, con mensaje distinto para respuesta **nueva** o **actualizada**.

### Vista del organizador

- Datos del asado y link para invitados.
- Cantidad de respuestas y tabla resumida (nombre, chico, vegetariano, apetito, elecciones).
- **Lista de compras** agrupada por **Carnicería**, **Verdulería** y **Almacén**, con cantidades.
- Botón para **copiar/descargar la lista como texto** listo para pegar en WhatsApp.
- Botón para refrescar.

## Reglas de negocio (definidas en la etapa 1)

Todas las constantes van en `config.py` para poder ajustarlas sin tocar la lógica.

### Opciones del formulario

| Categoría       | Opciones                                                                    | Sección de compra    |
| --------------- | --------------------------------------------------------------------------- | -------------------- |
| Vaca            | asado de tira, vacío, matambre, entraña, colita de cuadril, bife de chorizo | Carnicería           |
| Cerdo           | bondiola, matambre de cerdo, costillitas                                    | Carnicería           |
| Pollo           | pata muslo, alitas                                                          | Carnicería           |
| Achuras         | chorizo, morcilla, chinchulines, mollejas, riñón                            | Carnicería           |
| Acompañamientos | provoleta, verduras a la parrilla, choclo, ensalada                         | Almacén / Verdulería |

Automáticos (no se eligen): **pan** y **carbón**.

### Factor por persona

```
factor = FACTOR_APETITO[apetito] × (FACTOR_CHICO si es chico, si no 1)
```

- `FACTOR_APETITO`: poco 0.75 · normal 1.0 · mucho 1.3
- `FACTOR_CHICO`: 0.5

### Carne (vaca + cerdo + pollo)

- Base: **400 g de carne cruda por adulto** con apetito normal.
- Cada persona no vegetariana aporta `400 × factor` gramos, **repartidos en partes iguales entre los cortes que eligió**.
- El total por corte es la suma de los aportes de todos.
- Vegetarianos: 0 g de carne y de achuras.

Ejemplo: Ana (normal) elige vacío y bondiola → 200 g de vacío + 200 g de bondiola.

### Achuras (se suman aparte de la carne)

Por cada persona que la elige, multiplicado por su factor:

| Achura       | Cantidad por persona | Unidad de compra |
| ------------ | -------------------- | ---------------- |
| chorizo      | 1                    | unidades         |
| morcilla     | 0.5                  | unidades         |
| chinchulines | 60 g                 | gramos           |
| mollejas     | 60 g                 | gramos           |
| riñón        | 50 g                 | gramos           |

(Etapa 8: las cantidades de chinchulines, mollejas y riñón bajaron de 100 / 100 / 80 g a 60 / 60 / 50 g.)

Para el cálculo del carbón, chorizo y morcilla se convierten a peso: **100 g por unidad** cada uno (`PESO_CHORIZO`, `PESO_MORCILLA` en `config.py`).

### Acompañamientos

Por cada persona que lo elige, multiplicado por su factor. **Si la persona es vegetariana, su cantidad de acompañamientos se multiplica × 2** (compensa la falta de carne).

| Acompañamiento         | Cantidad por persona    | Sección    |
| ---------------------- | ----------------------- | ---------- |
| provoleta              | 0.5 (1 cada 2 personas; sin el 15 % extra) | Almacén    |
| verduras a la parrilla | 300 g                   | Verdulería |
| choclo                 | 1                       | Verdulería |
| ensalada               | 200 g de verdura        | Verdulería |

### Automáticos

- **Pan**: 120 g por persona (todos, incluidos vegetarianos), × factor. Sección: Almacén.
- **Carbón**: 1 kg de carbón por cada kg total de carne + achuras (chorizo y morcilla convertidos a peso), **en bolsas de 4 kg**. Sección: Almacén.
  - Se calcula sobre los kg **con el extra del 15 % ya aplicado, antes de redondear**.
  - Al carbón **no** se le aplica otro 15 %.

### Extra y redondeo

- A todas las cantidades calculadas (incluido el pan) se les aplica un **extra del 15 %** (`EXTRA = 0.15`) antes de redondear. Excepciones: el carbón (ver arriba) y la **provoleta** (`SIN_EXTRA` en `config.py`), porque se compra entera y el extra la inflaba (2 personas → 2 provoletas).
- Se redondea **el total de cada ítem**, nunca el aporte individual de cada persona.
- Redondeo **siempre hacia arriba**:
  - todo lo que se mide en gramos (cortes, achuras, verduras, pan): múltiplos de **10 g** (`REDONDEO_GRAMOS`). Así el redondeo casi no agrega nada y el margen lo da solo el 15 %, sin importar cuántas personas respondan ("verduras a la parrilla" y "ensalada" son ítems separados en Verdulería);
  - unidades (chorizo, morcilla, provoleta, choclo): entero;
  - carbón: bolsas enteras.
- Formato en pantalla y en el texto: menos de 1 kg en gramos ("460 g"); desde 1 kg, en kg con dos decimales ("1,38 kg").
- Un ítem que nadie eligió no aparece en la lista.

## Modelo de datos

```sql
CREATE TABLE IF NOT EXISTS asados (
    slug        TEXT PRIMARY KEY,
    nombre      TEXT NOT NULL,
    fecha       DATE,
    clave_admin TEXT NOT NULL,
    creado_en   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS respuestas (
    id              SERIAL PRIMARY KEY,
    asado_slug      TEXT NOT NULL REFERENCES asados(slug) ON DELETE CASCADE,
    nombre          TEXT NOT NULL,    -- tal como se escribió en el último envío (trim)
    nombre_clave    TEXT NOT NULL,    -- lower(trim(nombre)): identifica a la persona
    es_chico        BOOLEAN NOT NULL DEFAULT false,
    es_vegetariano  BOOLEAN NOT NULL DEFAULT false,
    apetito         TEXT NOT NULL CHECK (apetito IN ('poco','normal','mucho')),
    elecciones      JSONB NOT NULL,   -- {"vaca": [...], "cerdo": [...], "pollo": [...], "achuras": [...], "acompanamientos": [...]}
    actualizado_en  TIMESTAMPTZ DEFAULT now(),
    UNIQUE (asado_slug, nombre_clave)
);
```

La app crea las tablas al iniciar si no existen. El reenvío con el mismo nombre usa `INSERT ... ON CONFLICT (asado_slug, nombre_clave) DO UPDATE` (que también actualiza `nombre`). Normalizar el nombre (trim) antes de guardar. La función de guardado devuelve si la respuesta fue nueva o una actualización.

## Etapas

### Etapa 2 — Formulario y creación de asado, sin base de datos

- Crear la estructura del proyecto, `requirements.txt`, `.gitignore` (incluir `.streamlit/secrets.toml`, `.venv/`, `__pycache__/`) y `config.py`.
- Implementar la pantalla **Crear asado** y el **formulario del invitado** con el ruteo por URL.
- Guardar en memoria con un diccionario compartido entre sesiones (`@st.cache_resource`), detrás de funciones con la misma interfaz que tendrá `db.py`, para que la etapa 3 solo cambie la implementación.
- Verificación esperada: crear un asado, abrir el link en dos pestañas, enviar respuestas y comprobar que el reenvío con el mismo nombre actualiza.

### Etapa 3 — Conexión a Neon

- Implementar `db.py` con Postgres usando `st.connection("sql")`.
- Crear `.streamlit/secrets.toml.example` con este formato (valores ficticios):
  ```toml
  [connections.sql]
  url = "postgresql://usuario:password@host.neon.tech/basededatos?sslmode=require"
  ```
- Creación de tablas al iniciar.
- Explicame los pasos manuales en Neon (crear proyecto, copiar la cadena de conexión) y dónde pegarla.
- Verificación esperada: los datos persisten al reiniciar la app y los veo en el SQL Editor de Neon.

### Etapa 4 — Vista del organizador

- Pantalla del organizador con validación de clave, datos del asado, link para invitados y tabla de respuestas.
- Todavía sin lista de compras.

### Etapa 5 — Cálculo y lista de compras

- Implementar `calculo.py` con las reglas de negocio de arriba.
- Tests en `tests/test_calculo.py` que cubran al menos: un adulto normal con un corte; reparto entre varios cortes; chico; apetito poco/mucho; vegetariano (sin carne, acompañamientos × 2); extra del 15 %; redondeos; carbón en bolsas; ítems no elegidos que no aparecen.
- Mostrar la lista agrupada por sección en la vista del organizador y el botón de texto para WhatsApp.
- Verificación esperada: correr `pytest` y comparar un caso chico calculado a mano contra la app.

### Etapa 6 — Preparación para deploy

- `README.md` en español: qué hace la app, cómo correrla local, cómo configurar Neon y cómo deployar en Streamlit Community Cloud (incluido dónde pegar los secrets en la configuración de la app).
- Revisar que no haya secretos en el repo (`git status`, `.gitignore`, historial).
- Guiarme en el `git push` a un repo público y en el deploy en Streamlit Community Cloud. Esos pasos los hago yo; vos me decís qué hacer y qué verificar.
- Recordatorio en el README: Streamlit Community Cloud duerme la app tras 12 h sin visitas y Neon suspende la base sin uso; antes de una demo, abrir la app unos minutos antes.

### Etapa 7 — Estética (agregada después de la etapa 6)

- Tema "brasa" en `.streamlit/config.toml`: colores cálidos y bordes redondeados, con versión clara y oscura (`[theme.light]` / `[theme.dark]`). Por defecto sigue al sistema operativo y se cambia desde el menú ⋮ → Settings; Streamlit no permite cambiar el tema desde el código. Sin fuentes externas.
- Los nombres de comidas se muestran con mayúscula inicial (solo en pantalla y en el texto de WhatsApp; en `config.py` y en la base siguen en minúscula para no romper datos existentes).
- Crear asado: encabezado "Achurapp", links en tarjetas y botón para compartir el link de invitados por WhatsApp.
- Formulario del invitado: cortes y acompañamientos como chips (`st.pills`), apetito con control segmentado y emojis, vegetariano y chico/a como interruptores, cada categoría en una tarjeta con ícono.
- Vista del organizador: indicadores (respuestas, vegetarianos, chicos/as, kg de carne), pestañas "Lista de compras" y "Respuestas", secciones de compra en tarjetas y botón "Enviar por WhatsApp".
- WhatsApp: son links `https://wa.me/?text=...` que abren WhatsApp con el texto ya escrito. Es gratuito y no es una API: la app no se conecta a ningún servicio.
- Sin cambios en el cálculo, la base ni las reglas de negocio.

### Etapa 8 — Ajuste del cálculo

- Achuras a 60 / 60 / 50 g, redondeo de gramos a 10 g, formato g / kg con dos decimales, provoleta sin el 15 % extra (ya incorporado en las reglas de arriba).
- Actualizar los tests con los valores nuevos.

### Etapa 9 — Menú más detallado

- **Formulario sin `st.form`**: cada cambio se refleja al instante (hace falta para la ensalada). Visualmente igual.
- **Verduras a la parrilla** pasa a ser una categoría propia, en Verdulería, con opciones: morrón, cebolla, berenjena, zapallito, papa, batata y choclo.
  - Cada verdura elegida aporta **100 g por persona** × factor, con un **tope de 300 g por persona**: si elige más de tres, los 300 g se reparten en partes iguales.
  - El **choclo** va en esa sección del formulario pero se cuenta aparte, en unidades: 1 por persona × factor. No cuenta para el tope.
- **Ensalada** = ensalada criolla (lechuga, tomate y cebolla). Al elegirla aparece "¿Le sacamos algo?" con esos tres ingredientes. Los 200 g por persona × factor se reparten entre los ingredientes que sí quiere (al menos uno). En la lista, lechuga, tomate y cebolla van por separado en Verdulería, y la cebolla de la ensalada se suma con la de la parrilla en un solo renglón.
- **Vegetarianos**:
  - el título de "Acompañamientos" pasa a ser **"🌱 Tu menú"**;
  - en esa sección aparece **"Medallones (soja, lentejas, garbanzos)"**, solo si está activado Vegetariano/a: 1 por persona × factor (con el × 2 vegetariano, 2), en unidades, sección Almacén;
  - siguen contando **× 2 en todos los acompañamientos y verduras** (incluidos provoleta y medallones);
  - tiene que elegir al menos una opción entre verduras y su menú.
- **Datos viejos**: el cálculo ignora opciones que ya no existen, y se borran las respuestas de prueba de Neon (el usuario lo hace desde el SQL Editor, guiado).

### Etapa 10 — Respuesta privada y cierre del formulario

- **Link personal por invitado**: al responder por primera vez, cada invitado recibe un link propio (`?asado=<slug>&invitado=<token>`, token con `secrets.token_urlsafe(8)`), con aviso de guardarlo y botón para mandárselo por WhatsApp.
  - Con el link personal, el formulario aparece con sus respuestas cargadas y puede editarlas. El nombre no se cambia.
  - Con el link del grupo, un nombre que ya respondió **no pisa** la respuesta existente: se muestra "Ya hay una respuesta con ese nombre. Si sos vos, entrá con tu link personal; si no, agregá tu apellido." Esto reemplaza la regla anterior de "reenviar con el mismo nombre actualiza".
  - Si alguien pierde su link personal, no puede editar su respuesta.
- **Cerrar el formulario**: interruptor "Formulario abierto" en la vista del organizador, que se puede volver a abrir. Con el formulario cerrado, los links del grupo y los personales muestran "El formulario está cerrado: ya se hicieron las compras 🛒".
- Modelo de datos: `respuestas.token TEXT` y `asados.cerrado BOOLEAN NOT NULL DEFAULT false`, agregadas con `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` al iniciar.

## Primer paso

Antes de escribir código, confirmame en pocas líneas que entendiste el alcance y mencioname cualquier ambigüedad que veas en las reglas de negocio. Después arrancá con la **Etapa 2**.

(Hecho: las ambigüedades se resolvieron y las decisiones ya están incorporadas arriba.)
