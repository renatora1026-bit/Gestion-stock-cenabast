# --- BLOQUE DE PROCESAMIENTO ICP (Copia esto sobre el anterior) ---
if f_icp:
    try:
        # TÉCNICA 1: Fuerza bruta como HTML (La más probable para archivos de portales)
        f_icp.seek(0)
        data_icp = pd.read_html(f_icp)[0]
        st.success("✅ ICP Cenabast sincronizado (Formato Web detectado)")
    except:
        try:
            # TÉCNICA 2: Excel Estándar
            f_icp.seek(0)
            data_icp = pd.read_excel(f_icp)
            st.success("✅ ICP Cenabast sincronizado (Excel detectado)")
        except:
            try:
                # TÉCNICA 3: CSV con separador de sistema chileno
                f_icp.seek(0)
                data_icp = pd.read_csv(f_icp, sep=";", encoding='latin1')
                st.success("✅ ICP Cenabast sincronizado (CSV detectado)")
            except Exception as e:
                st.error("🚨 Sigue resistiéndose. Último recurso: Abre el archivo en tu Mac y guárdalo específicamente como 'Libro de Excel (.xlsx)'.")
