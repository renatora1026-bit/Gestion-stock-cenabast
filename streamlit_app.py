import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN IA (Tu clave confirmada) ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 SSASUR (CSV)", type=["csv"])
with col2: f_icp = st.file_uploader("📦 CENABAST (Excel o CSV)", type=["xlsx", "xls", "csv"])

if f_ssasur and f_icp:
    with st.spinner('🤖 IA analizando el Arsenal de CENABAST...'):
        try:
            # 1. Leer SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # 2. Leer CENABAST (Manejo inteligente de Excel)
            if f_icp.name.endswith(('xlsx', 'xls')):
                df_c = pd.read_excel(f_icp)
            else:
                df_c = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
            
            # Limpiamos filas vacías al inicio (típico en Excels de Cenabast)
            df_c = df_c.dropna(how='all').iloc[2:200] 
            datos_cenabast = df_c.astype(str).to_string(index=False)

            # 3. Filtrar Críticos (< 0.5 meses)
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(12)
            
            if not criticos.empty:
                st.subheader("⚠️ Estado Logístico Real")
                
                def consultar_ia(prod):
                    # Prompt reforzado para evitar errores de interpretación
                    prompt = f"""
                    Eres un Q.F. en Chile. Busca el fármaco '{prod}' en estos datos de CENABAST:
                    {datos_cenabast}
                    
                    Dime el ESTADO (ej: APROBADO, ENTREGADO). Si no está, di 'NO EN LISTA'. 
                    Responde solo con la palabra del estado.
                    """
                    try:
                        res = model.generate_content(prompt)
                        return res.text.strip().upper()
                    except:
                        return "CONSULTAR"

                criticos['Estado Real (Cenabast)'] = criticos['Producto'].apply(consultar_ia)
                
                # Tabla profesional con colores
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real (Cenabast)']].style.applymap(
                    lambda x: 'background-color: #1b5e20; color: white' if x in ['APROBADO', 'ENTREGADO', 'PROGRAMADO'] else 
                              ('background-color: #b71c1c; color: white' if x == 'NO EN LISTA' else ''),
                    subset=['Estado Real (Cenabast)']
                ))
            else:
                st.success("✅ Todo el stock parece estar en orden.")
                
        except Exception as e:
            st.error(f"Error técnico: {e}. Revisa el formato del archivo.")
