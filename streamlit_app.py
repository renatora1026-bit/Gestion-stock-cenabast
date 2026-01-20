import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN IA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- CARGA DE ARCHIVOS ---
f_ssasur = st.file_uploader("📥 1. Cargar SSASUR (CSV)", type=["csv"])
f_icp = st.file_uploader("📦 2. Cargar CENABAST (CSV)", type=["csv"])

if f_ssasur and f_icp:
    with st.spinner('🤖 Inteligencia Artificial analizando disponibilidad...'):
        try:
            # 1. Identificamos críticos en SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            # Tomamos los 10 más críticos
            criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(10)
            lista_farma = criticos['Producto'].tolist()

            # 2. Leemos CENABAST como texto bruto (Sin columnas)
            texto_cenabast = f_icp.getvalue().decode('latin1', errors='ignore')
            # Limitamos el texto para no saturar la IA
            fragmento_cenabast = texto_cenabast[:20000] 

            # 3. Consulta maestra a Gemini
            prompt = f"""
            Actúa como el encargado de abastecimiento del Hospital Puerto Saavedra.
            Tengo este reporte de CENABAST en texto bruto:
            ---
            {fragmento_cenabast}
            ---
            
            Necesito que busques el estado real de estos fármacos: {lista_farma}.
            Para cada uno dime si aparece como 'ENTREGADO', 'APROBADO', 'SUSPENDIDO' o si no tiene información.
            
            Responde con una tabla simple que tenga estas columnas: 
            Producto | Estado en CENABAST | Detalle Adicional
            """

            response = model.generate_content(prompt)

            # 4. Mostramos el resultado directo
            st.subheader("📋 Informe de Disponibilidad Real")
            st.markdown(response.text)
            
            with st.expander("Ver datos originales de SSASUR"):
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

        except Exception as e:
            st.error(f"Se produjo un error: {e}")
