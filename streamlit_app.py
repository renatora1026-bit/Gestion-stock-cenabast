import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN IA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- 2. CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 SSASUR (CSV)", type=["csv"])
with col2: f_icp = st.file_uploader("📦 CENABAST (Excel o CSV)", type=["xlsx", "xls", "csv"])

# --- 3. PROCESAMIENTO ---
if f_ssasur and f_icp:
    with st.spinner('🤖 IA Escaneando Arsenal de CENABAST...'):
        try:
            # Procesar SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # Procesar CENABAST con mayor profundidad
            if f_icp.name.endswith(('xlsx', 'xls')):
                df_c = pd.read_excel(f_icp)
            else:
                df_c = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
            
            # TRUCO: Saltamos las primeras filas vacías si existen y tomamos 300 registros
            df_c = df_c.dropna(how='all').iloc[5:305] 
            texto_referencia = df_c.astype(str).to_string(index=False)

            # Filtrar críticos
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(12)
            
            if not criticos.empty:
                st.subheader("⚠️ Estado Logístico Real (IA)")
                
                def buscar_farmaco_ia(producto):
                    # Prompt optimizado para evitar el "SIN INFO"
                    prompt = f"""
                    Como experto farmacéutico, analiza si '{producto}' está en estos datos de CENABAST:
                    {texto_referencia}
                    
                    Busca por nombre genérico. Si lo encuentras, responde SOLO con su estado: 
                    'APROBADO', 'ENTREGADO', 'PROGRAMADO' o 'RECHAZADO'. 
                    Si no hay rastro, responde 'NO EN LISTA'.
                    """
                    try:
                        response = model.generate_content(prompt)
                        res = response.text.strip().upper()
                        return res if len(res) < 20 else "ANALIZAR"
                    except:
                        return "ERROR"

                criticos['Estado Real (Cenabast)'] = criticos['Producto'].apply(buscar_farmaco_ia)
                
                # Tabla con colores según gestión
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real (Cenabast)']].style.applymap(
                    lambda x: 'background-color: #1b5e20; color: white' if x in ['APROBADO', 'ENTREGADO', 'PROGRAMADO'] else 
                              ('background-color: #b71c1c; color: white' if x == 'NO EN LISTA' else ''),
                    subset=['Estado Real (Cenabast)']
                ))
            else:
                st.success("✅ No hay alertas de quiebre.")
                
        except Exception as e:
            st.error(f"Error: {e}")
