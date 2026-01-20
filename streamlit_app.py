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
    with st.spinner('🤖 Inteligencia Artificial sincronizando datos...'):
        try:
            # Procesar SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # Procesar CENABAST (Mejoramos la lectura de Excel)
            if f_icp.name.endswith(('xlsx', 'xls')):
                df_c = pd.read_excel(f_icp)
            else:
                df_c = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
            
            # Limpieza básica para que la IA no se maree
            df_c = df_c.dropna(how='all').head(200) # Tomamos los primeros 200 registros
            contexto_icp = df_c.astype(str).to_string(index=False)

            # Filtrar críticos (< 0.5 meses)
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(12)
            
            if not criticos.empty:
                st.subheader("⚠️ Estado Real de Fármacos Críticos")
                
                def validar_con_ia(producto):
                    # Prompt ultra-específico para evitar el error "REINTENTAR"
                    prompt = f"""
                    Como experto en farmacia hospitalaria, busca el fármaco '{producto}' en estos datos:
                    {contexto_icp}
                    
                    Dime su ESTADO (ej: APROBADO, PENDIENTE, ENTREGADO). 
                    Si no lo ves, responde 'NO IDENTIFICADO'. 
                    Responde solo UNA palabra.
                    """
                    try:
                        response = model.generate_content(prompt)
                        return response.text.strip().upper()
                    except:
                        return "SIN INFO"

                # Ejecución
                criticos['Estado Real (Cenabast)'] = criticos['Producto'].apply(validar_con_ia)
                
                # Formato visual profesional
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real (Cenabast)']].style.applymap(
                    lambda x: 'background-color: #1b5e20; color: white' if x in ['APROBADO', 'ENTREGADO', 'DESPACHADO'] else 
                              ('background-color: #b71c1c; color: white' if x == 'NO IDENTIFICADO' else ''),
                    subset=['Estado Real (Cenabast)']
                ))
            else:
                st.success("✅ Todo el stock crítico está bajo control.")
                
        except Exception as e:
            st.error(f"Error de lectura: {e}. Asegúrate de subir archivos válidos.")
