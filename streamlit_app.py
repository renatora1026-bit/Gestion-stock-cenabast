import streamlit as st
import pandas as pd

st.set_page_config(page_title="Radar Saavedra", layout="wide")
st.title("🚀 Radar de Stock - Hospital Puerto Saavedra")
st.write("Gestionado por QF Renato Rozas")

archivo = st.file_uploader("Sube tu SSASUR para analizar", type=["csv"])

if archivo:
    try:
        # Leemos con el formato de SSASUR
        df = pd.read_csv(archivo, sep=";", encoding='latin1')
        
        # SOLUCIÓN AL ERROR: Convertimos 'Saldo Meses' a número, ignorando errores de texto
        df['Saldo Meses'] = pd.to_numeric(df['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
        df = df.dropna(subset=['Saldo Meses']) # Limpiamos filas vacías
        
        st.success("¡Archivo procesado con éxito!")

        # Semáforo Inteligente
        def color_semaforo(val):
            if val < 0.5: return 'background-color: #ff4b4b; color: white' # Rojo
            elif val < 1.0: return 'background-color: #ffa500; color: black' # Naranja
            return 'background-color: #28a745; color: white' # Verde

        # Mostramos los resultados ordenados por los más críticos
        st.subheader("🚨 Prioridades de Abastecimiento")
        df_mostrar = df[['Producto', 'Saldo Actual', 'Saldo Meses']].sort_values('Saldo Meses')
        st.dataframe(df_mostrar.style.applymap(color_semaforo, subset=['Saldo Meses']), use_container_width=True)

    except Exception as e:
        st.error(f"Error de lectura: {e}")
