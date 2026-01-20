import streamlit as st
import pandas as pd

st.set_page_config(page_title="Radar QF Saavedra", layout="wide", page_icon="🚥")

st.title("🚥 Radar de Abastecimiento Crítico")
st.write("Hospital de Puerto Saavedra - Gestión QF Renato Rozas")

# 1. Aseguramos que el requirements.txt tenga: streamlit, pandas, openpyxl, plotly

archivos = st.file_uploader("Sube aquí tus reportes (SSASUR, ICP o Arsenal)", type=["csv", "xlsx", "xlsm"], accept_multiple_files=True)

if archivos:
    data_consolidada = []
    
    for f in archivos:
        try:
            # Lógica de lectura robusta
            if f.name.endswith('.csv'):
                # Probamos primero con punto y coma (SSASUR) y luego con coma
                try:
                    df = pd.read_csv(f, sep=";", encoding='latin1')
                except:
                    df = pd.read_csv(f, sep=",", encoding='utf-8')
            else:
                df = pd.read_excel(f, engine='openpyxl')
            
            st.success(f"✅ Cargado: {f.name}")
            
            # Identificamos si es SSASUR para el semáforo
            if 'Saldo Meses' in df.columns and 'Producto' in df.columns:
                st.subheader(f"📊 Análisis de Stock: {f.name}")
                
                # Definimos el Semáforo
                def color_estado(val):
                    if val < 0.5: return 'background-color: #ff4b4b; color: white' # Rojo
                    elif val < 1.0: return 'background-color: #ffa500; color: black' # Naranja
                    return 'background-color: #28a745; color: white' # Verde

                # Mostramos solo lo crítico arriba
                criticos = df[['Producto', 'Saldo Actual', 'Saldo Meses', 'Consumo Promedio Mensual']].sort_values('Saldo Meses')
                st.dataframe(criticos.style.applymap(color_estado, subset=['Saldo Meses']))
                
        except Exception as e:
            st.error(f"❌ Error en {f.name}: {e}")

else:
    st.info("👋 Hola Renato. Sube los archivos que descargaste hoy para empezar el cruce de datos.")
