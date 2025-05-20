import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# ─── 1) Configuración general ───────────────────────────────────────────────
st.set_page_config(layout="wide")

# Mapeo de módulos a rutas CSV y a survey IDs (para tokens)
cuestionarios_csv = {
    "Módulo 1": "Encuestas/M1 (367996).csv",
    "Módulo 2": "Encuestas/M2 (762638).csv",
    "Módulo 3": "Encuestas/M3 (156244).csv",
    "Módulo 4": "Encuestas/M4 (238547).csv",
    "Módulo 5": "Encuestas/M5 (381421).csv",
    "Módulo 6": "Encuestas/M6 (865393).csv",
    "Módulo 7": "Encuestas/M7 (988223).csv",
    "Módulo 8": "Encuestas/M8 (429228).csv",
}
survey_ids = {
    "Módulo 1": 367996,
    "Módulo 2": 762638,
    "Módulo 3": 156244,
    "Módulo 4": 238547,
    "Módulo 5": 381421,
    "Módulo 6": 865393,
    "Módulo 7": 988223,
    "Módulo 8": 429228,
}

# ─── 2) Carga de CSV (respuestas) ──────────────────────────────────────────
@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    """Lee el CSV de respuestas y lo devuelve en un DataFrame."""
    return pd.read_csv(file_path, sep=',', encoding='utf-8', on_bad_lines='skip')

# ─── 3) Carga de tokens desde MySQL ────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_tokens_from_db(survey_id: int) -> pd.DataFrame:
    """
    Conecta a MySQL, lee token+email de lime_tokens_<survey_id>,
    y devuelve un DataFrame.
    """
    cfg = st.secrets["mysql"]
    conn_str = (
        f"mysql+pymysql://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    )
    engine = create_engine(conn_str)
    table = f"lime_tokens_{survey_id}"
    query = f"SELECT token, email FROM {table}"
    return pd.read_sql(query, engine)

# ─── 4) Interfaz y lógica ─────────────────────────────────────────────────
with st.container():
    # Encabezado
    st.image("Logo2.jpg", use_container_width=True)
    st.markdown("<h1 style='color:black;'>Consulta de módulos LEPPODS</h1>", unsafe_allow_html=True)

    # Sidebar: login + módulo
    with st.sidebar:
        st.markdown("<h2 style='color:black;'>Acceso seguro</h2>", unsafe_allow_html=True)
        mod = st.selectbox("Seleccione el módulo:", list(cuestionarios_csv.keys()))
        email_input = st.text_input("Correo electrónico:").strip().lower()
        token_input = st.text_input("Token (contraseña):", type="password").strip()

    # Validar campos
    if not email_input or not token_input:
        st.info("Por favor ingresa tu correo y tu token.")
        st.stop()

    # 4.1) Autenticación de token
    survey_id = survey_ids[mod]
    df_tokens = load_tokens_from_db(survey_id)
    df_tokens["email"] = df_tokens["email"].astype(str).str.strip().str.lower()
    df_tokens["token"] = df_tokens["token"].astype(str).str.strip()

    auth = df_tokens[
        (df_tokens["email"] == email_input) &
        (df_tokens["token"] == token_input)
    ]
    if auth.empty:
        st.error("✋ Credenciales inválidas. Verifica correo o token.")
        st.stop()

    st.success(f"🔓 Acceso concedido como **{email_input}** en **{mod}**")

    # 4.2) Cargar respuestas desde CSV
    csv_path = cuestionarios_csv[mod]
    df = load_data(csv_path)

    # Identificar columna de correo
    cols = df.columns.tolist()
    email_cols = [c for c in cols if "correo" in c.lower()]
    if not email_cols:
        st.error("No se encontró columna de correo en el CSV.")
        st.stop()
    email_col = email_cols[0]

    # Normalizar y filtrar respuestas
    df[email_col] = df[email_col].astype(str).str.strip().str.lower()
    df_filtrado = df[df[email_col] == email_input]

    if df_filtrado.empty:
        st.warning("No hay respuestas registradas para tu correo en este módulo.")
        st.stop()

    # 4.3) Mostrar resumen y respuestas
    st.success(f"📊 Respuestas encontradas: {len(df_filtrado)}")

    # Tarjetas resumen
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div style="background-color:#2C5234;padding:15px;border-radius:10px;">
            <h4 style="color:#ffffff;">Correo:</h4>
            <p style="color:#ffffff;">{email_input}</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="background-color:#2C5234;padding:15px;border-radius:10px;">
            <h4 style="color:#ffffff;">Token:</h4>
            <p style="color:#ffffff;">{token_input}</p>
        </div>""", unsafe_allow_html=True)

    # Columnas a ocultar
    ocultar = [
        'Ultima pagina','Idioma de Inicio','Semilla','Código de acceso',
        'Dirección IP','¿Cuál es tu municipio?','Fecha en que se envió',
        'URL de referencia','ID de la respuesta', email_col
    ]

    # Expanders con formato original
    for _, row in df_filtrado.iterrows():
        title = f"📋 Respuesta ID: {row['ID de la respuesta']}"
        with st.expander(title):
            respuestas = {
                col: row[col] for col in df_filtrado.columns
                if col not in ocultar and not pd.isna(row[col])
            }
            for preg, resp in respuestas.items():
                st.markdown(f"""
                <div style="background-color:#526436;padding:12px;border-radius:8px;margin-bottom:10px;">
                  <h5 style="color:#ffffff;">{preg}</h5>
                  <div style="background-color:#ffffff;padding:8px;border-radius:5px;color:#000000;">
                    {resp}
                  </div>
                </div>""", unsafe_allow_html=True)