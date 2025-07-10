import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from datetime import datetime
import time

# ----------- ESTILO VISUAL (FONDO CON IMAGEN LOCAL) -----------
def set_bg_from_local(file):
    with open(file, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
    css = f'''
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/png;base64,{encoded}");
            background-repeat: no-repeat;
            background-position: center;
            background-size: 400px;
            background-attachment: fixed;
            opacity: 0.98;
        }}
        </style>
    '''
    st.markdown(css, unsafe_allow_html=True)

set_bg_from_local("LOGO.png")

# ----------- Cargar estilos generales -----------
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ----------- Encabezado institucional -----------
st.markdown("""
    <div style='background-color: #003f5c; padding: 10px 0; margin-bottom: 20px;'>
        <h1 style='color: white; font-family:Segoe UI;'>Sistema de Registro de Muestras de Agua</h1>
    </div>
""", unsafe_allow_html=True)

# ----------- AUTENTICACIÓN ----------- 
hashed_passwords = [
    '$2b$12$Knmn73uGEngJlIcU0cK4IehB0uYEF4uQxdpHiL5QN1gVKcVYU7vFe'
]

config = {
    'credentials': {
        'usernames': {
            'julian': {
                'email': 'julian@empresa.com',
                'name': 'Julian',
                'password': hashed_passwords[0]
            }
        }
    },
    'cookie': {
        'expiry_days': 1,
        'key': 'clave_firma',
        'name': 'nombre_cookie'
    }
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

st.set_page_config(page_title="Registro de Muestras de Agua", layout="centered")

login_result = authenticator.login("main")
if login_result is not None:
    name, authentication_status, username = login_result
else:
    name = authentication_status = username = None

if authentication_status:
    authenticator.logout("Cerrar sesión", location="main")

    st.markdown("---")
    st.markdown("### Datos generales")

    if "data" not in st.session_state:
        st.session_state.data = []

    with st.form("formulario"):
        fecha = st.date_input("Fecha")
        hora = st.time_input("Hora")
        quien_muestrea = st.text_input("¿Quién realizó la muestra?")

        st.markdown("### Dispositivo de muestra")
        dispositivo = st.selectbox("Seleccione el dispositivo", ["Manguera", "Canal", "Grifo"])

        st.markdown("### Análisis a realizar")
        fisico_quimico = st.radio("¿Físico Químico?", ["Sí", "No"], horizontal=True)
        microbiologico_1 = st.radio("¿Microbiológico 1?", ["Sí", "No"], horizontal=True)
        microbiologico_2 = st.radio("¿Microbiológico 2?", ["Sí", "No"], horizontal=True)

        st.markdown("### Parámetros In Situ")
        tipo_agua = st.selectbox("Tipo de Agua", ["AP - Agua Potable", "ASP - Agua Superficial"])
        ph = st.number_input("pH", format="%.2f")
        cloro = st.number_input("Cloro (mg/L)", format="%.2f")
        temperatura = st.number_input("Temperatura (°C)", format="%.2f")
        observaciones = st.text_area("Observaciones")
        tipo_muestra = st.selectbox("Tipo de muestra", ["I - Interna", "R - Punto de red", "E - Externa"])

        submitted = st.form_submit_button("Guardar")
        if submitted:
            tipo_letra = tipo_muestra.split(" ")[0]
            año = fecha.strftime("%y")
            mes = fecha.strftime("%m")
            prefijo = f"{tipo_letra}{año}-{mes}"

            contador = 1
            if st.session_state.data:
                existentes = [row for row in st.session_state.data if row.get("Código", "").startswith(prefijo)]
                contador = len(existentes) + 1

            codigo_unico = f"{prefijo}{contador:03d}"

            nueva_fila = {
                "Código": codigo_unico,
                "Fecha": fecha.strftime("%Y-%m-%d"),
                "Hora": hora.strftime("%H:%M"),
                "Quién Muestra": quien_muestrea,
                "Dispositivo de Muestra": dispositivo,
                "Físico Químico": fisico_quimico,
                "Microbiológico 1": microbiologico_1,
                "Microbiológico 2": microbiologico_2,
                "Tipo de Agua": tipo_agua,
                "pH": ph,
                "Cloro (mg/L)": cloro,
                "Temperatura (°C)": temperatura,
                "Observaciones": observaciones,
                "Tipo de Muestra": tipo_muestra
            }

            with st.spinner("Guardando datos..."):
                st.session_state.data.append(nueva_fila)
                time.sleep(1)
            st.success(f"✅ Datos guardados. Código asignado: {codigo_unico}")

    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        st.markdown("---")
        st.subheader("Muestras registradas")
        st.dataframe(df, use_container_width=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Registro")
        st.download_button("⬇️ Descargar archivo Excel", output.getvalue(), file_name="registro_muestras.xlsx")

        st.markdown("---")
        st.subheader("Gráficas de Parámetros")

        fig1, ax1 = plt.subplots()
        sns.lineplot(data=df, x="Fecha", y="pH", marker="o", ax=ax1)
        ax1.axhline(9.5, color='r', linestyle='--', label='Máximo permitido')
        ax1.set_title("Valores de pH")
        ax1.set_ylabel("pH")
        ax1.legend()
        st.pyplot(fig1)

        fig2, ax2 = plt.subplots()
        sns.lineplot(data=df, x="Fecha", y="Cloro (mg/L)", marker="o", ax=ax2)
        ax2.axhline(2.0, color='r', linestyle='--', label='Máximo permitido')
        ax2.set_title("Valores de Cloro (mg/L)")
        ax2.set_ylabel("mg/L")
        ax2.legend()
        st.pyplot(fig2)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.9em; color: gray;'>Versión 1.0 - Mateo tu papá, Mateo el pro. Aguas de Facatativá © 2025</p>", unsafe_allow_html=True)

elif authentication_status is False:
    st.error("❌ Usuario o contraseña incorrectos")
elif authentication_status is None:
    st.warning("🔐 Por favor, inicia sesión para continuar")


