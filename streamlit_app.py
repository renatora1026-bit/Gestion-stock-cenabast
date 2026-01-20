import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra v2", layout="wide")
st.title("🚀 Radar de Abastecimiento IA")
st.markdown("Hospital Puerto Saavedra | **Nueva Estrategia Semántica**")

f_ssasur = st.file_uploader("📥 1. Sube SSASUR", type=["csv"])
f_icp = st.file_uploader("📦 2. Sube CENABAST", type=["csv"])

if f_ssasur and f_icp:
    with st.spinner('🤖 Analizando datos...'):
        try:
            # 1. Leer SSASUR para detectar críticos
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(8)
            lista_criticos = criticos['Producto'].tolist()

            # 2. Leer CENABAST como TEXTO BRUTO (No como tabla)
            # Esto evita errores de columnas, tildes y formatos.
            bytes_cenabast = f_icp.getvalue()
            texto_cenabast = bytes_cenabast.decode('latin1', errors='ignore')

            # 3. La IA hace el trabajo de "ojo humano"
            prompt = f"""
            Eres el Jefe de Farmacia del Hospital Puerto Saavedra. 
            Tengo este reporte de CENABAST (texto bruto):
            ---
            {texto_cenabast[:15000]} 
            ---
            Necesito saber el estado de estos fármacos críticos: {lista_criticos}
            
            Para cada uno, busca en el texto el SEMAFORO o ESTADO DEL MATERIAL.
            Devuélveme una tabla con: Fármaco | Estado en CENABAST | Observación corta.
            Si no lo encuentras, pon 'Sin información'.
            """
            
            response = model.generate_content(prompt)
            
            # 4. Mostrar el resultado directo de la IA
            st.subheader("📋 Informe de Disponibilidad Real (Análisis IA)")
            st.markdown(response.text)
            
            st.divider()
            st.write("🔍 **Datos detectados en SSASUR como críticos:**")
            st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

        except Exception as e:
            st.error(f"Error inesperado: {e}")
