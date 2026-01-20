import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

# --- 1. CONFIGURACIÓN IA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")

# --- 2. CARGA DE ARCHIVOS ---
f_ssasur = st.file_uploader("📥 Cargar SSASUR", type=["csv"])
f_icp = st.file_uploader("📦 Cargar CENABAST", type=["csv"])

if f_ssasur and f_icp:
    with st.spinner('🤖 Analizando estructuras...'):
        try:
            # Leer SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # --- MOTOR DE BÚSQUEDA CENABAST ---
            # Leemos el archivo bruto
            raw_data = f_icp.getvalue().decode('latin1').splitlines()
            
            # Buscamos en qué línea está el encabezado real
            start_line = 0
            for i, line in enumerate(raw_data):
                if "SEMAFORO" in line:
                    start_line = i
                    break
            
            # Cargamos desde esa línea encontrada
            f_icp.seek(0)
            df_c = pd.read_csv(f_icp, sep=';', skiprows=start_line, encoding='latin1')
            
            # Limpieza de columnas
            df_c.columns = [str(c).strip().upper() for c in df_c.columns]
            
            # Identificamos columnas por nombre real (ya que ahora las limpiamos bien)
            # Usamos 'NOMBRE GENERICO' y 'SEMAFORO'
            col_farma = 'NOMBRE GENERICO'
            col_estado = 'ESTADO DEL MATERIAL'
            col_sem = 'SEMAFORO'

            # Preparamos contexto para Gemini
            contexto_ia = df_c[[col_farma, col_sem, col_estado]].dropna(subset=[col_farma]).head(200).to_string(index=False)

            # Filtramos críticos
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(12)
            
            if not criticos.empty:
                st.subheader("⚠️ Estado Real en CENABAST")
                
                def consultar_ia(farma):
                    prompt = f"Basado en esta lista de CENABAST:\n{contexto_ia}\n\n¿Cual es el estado de '{farma}'? Responde solo una palabra o frase corta del estado. Si no está di 'SIN INFO'."
                    try:
                        res = model.generate_content(prompt)
                        return res.text.strip().upper()
                    except: return "ERROR"

                criticos['Estado Real'] = criticos['Producto'].apply(consultar_ia)
                
                # Mostrar Tabla
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real']].style.applymap(
                    lambda x: 'background-color: #1b5e20; color: white' if any(p in str(x) for p in ['ENTREGADO', 'APROBADO']) else 
                              ('background-color: #b71c1c; color: white' if 'SIN' in str(x) else ''),
                    subset=['Estado Real']
                ))
            else:
                st.success("✅ Stock al día.")

        except Exception as e:
            st.error(f"Fallo en el escaneo: {e}")
            # Esto nos dirá qué está viendo la app realmente
            if 'df_c' in locals(): st.write("Columnas leídas:", df_c.columns.tolist())
