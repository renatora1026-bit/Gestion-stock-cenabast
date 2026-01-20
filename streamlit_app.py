import streamlit as st
import pandas as pd

st.title("🚀 Radar de Stock - Hospital Puerto Saavedra")
st.write("Hola Renato, si ves esto, ¡la app ya está viva!")

archivo = st.file_uploader("Sube tu SSASUR para probar", type=["csv"])

if archivo:
    try:
        # Forzamos la lectura que usa SSASUR (punto y coma y latin1)
        df = pd.read_csv(archivo, sep=";", encoding='latin1')
        st.success("¡Archivo cargado correctamente!")
        
        # Semáforo rápido
        if 'Saldo Meses' in df.columns:
            def color_semaforo(val):
                color = 'red' if val < 0.5 else 'green'
                return f'background-color: {color}'
            
            st.dataframe(df[['Producto', 'Saldo Meses']].style.applymap(color_semaforo, subset=['Saldo Meses']))
    except Exception as e:
        st.error(f"Error de lectura: {e}")
