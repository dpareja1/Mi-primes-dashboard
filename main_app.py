import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Energía Renovable", layout="wide")

# Título
st.title("⚡ Análisis Exploratorio: Plantas de Energía Renovable")

# --- SIDEBAR: CARGA DE ARCHIVOS ---
st.sidebar.header("Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Sube tu archivo CSV aquí", type=["csv"])

# Función de carga con manejo de errores y caché
@st.cache_data
def load_data(file):
    try:
        # Intentar leer el archivo CSV
        df = pd.read_csv(file)
        
        # Limpieza básica: Convertir fecha a datetime si existe la columna
        if 'Fecha_Entrada_Operacion' in df.columns:
            df['Fecha_Entrada_Operacion'] = pd.to_datetime(df['Fecha_Entrada_Operacion'])
            
        return df
    except Exception as e:
        # Retornar el error para manejarlo fuera
        return str(e)

# --- LÓGICA PRINCIPAL ---
if uploaded_file is not None:
    # 1. Cargar datos
    data_result = load_data(uploaded_file)

    # 2. Verificar si hubo error (si el resultado es un string, es un mensaje de error)
    if isinstance(data_result, str):
        st.error(f"❌ Hubo un error al procesar el archivo: {data_result}")
    else:
        df = data_result
        st.success("✅ Archivo cargado exitosamente.")

        # --- VERIFICACIÓN DE COLUMNAS REQUERIDAS ---
        # Verificamos que existan las columnas clave para que no falle el resto del código
        required_columns = ["Tecnologia", "Estado_Actual", "Capacidad_Instalada_MW", "Operador"]
        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            st.error(f"El archivo subido no tiene las columnas requeridas: {', '.join(missing_cols)}")
        else:
            # ==========================================
            # AQUI COMIENZA EL DASHBOARD (FILTROS Y GRÁFICOS)
            # ==========================================
            
            # --- FILTROS ---
            st.sidebar.header("Filtros")

            # Filtro por Tecnología
            tecnologias = st.sidebar.multiselect(
                "Seleccionar Tecnología:",
                options=df["Tecnologia"].unique(),
                default=df["Tecnologia"].unique()
            )

            # Filtro por Estado
            estados = st.sidebar.multiselect(
                "Estado de la Planta:",
                options=df["Estado_Actual"].unique(),
                default=df["Estado_Actual"].unique()
            )

            # Aplicar filtros
            if not tecnologias or not estados:
                st.warning("Por favor selecciona al menos una tecnología y un estado.")
                st.stop()

            df_selection = df.query(
                "Tecnologia == @tecnologias & Estado_Actual == @estados"
            )

            # --- KPIs PRINCIPALES ---
            st.markdown("### Métricas Generales")
            col1, col2, col3, col4 = st.columns(4)

            total_capacidad = df_selection["Capacidad_Instalada_MW"].sum()
            
            # Manejo de error si la columna no existe o está vacía para promedios
            if "Eficiencia_Planta_Pct" in df.columns:
                promedio_eficiencia = df_selection["Eficiencia_Planta_Pct"].mean()
            else:
                promedio_eficiencia = 0

            if "Inversion_Inicial_MUSD" in df.columns:
                total_inversion = df_selection["Inversion_Inicial_MUSD"].sum()
            else:
                total_inversion = 0
                
            conteo_plantas = df_selection.shape[0]

            col1.metric("Capacidad Total (MW)", f"{total_capacidad:,.2f}")
            col2.metric("Eficiencia Promedio", f"{promedio_eficiencia:.1f}%")
            col3.metric("Inversión Total (MUSD)", f"${total_inversion:,.2f}")
            col4.metric("Total Plantas", conteo_plantas)

            st.markdown("---")

            # --- VISUALIZACIONES ---
            
            try:
                # 1. Capacidad por Operador y Tecnología
                st.subheader("1. Distribución de Capacidad por Operador")
                fig_bar = px.bar(
                    df_selection, 
                    x="Operador", 
                    y="Capacidad_Instalada_MW", 
                    color="Tecnologia",
                    title="Capacidad Instalada por Operador (MW)",
                    barmode="group",
                    template="plotly_white"
                )
                st.plotly_chart(fig_bar, use_container_width=True)

                col_charts_1, col_charts_2 = st.columns(2)

                with col_charts_1:
                    # 2. Relación Inversión vs Generación
                    if "Inversion_Inicial_MUSD" in df.columns and "Generacion_Diaria_MWh" in df.columns:
                        st.subheader("2. Inversión vs. Generación Diaria")
                        fig_scatter = px.scatter(
                            df_selection,
                            x="Inversion_Inicial_MUSD",
                            y="Generacion_Diaria_MWh",
                            color="Tecnologia",
                            size="Capacidad_Instalada_MW",
                            hover_data=df_selection.columns[:5], # Tooltip básico
                            title="Relación Costo-Beneficio (Tamaño = Capacidad MW)"
                        )
                        st.plotly_chart(fig_scatter, use_container_width=True)
                    else:
                        st.info("Faltan columnas para el gráfico de dispersión.")

                with col_charts_2:
                    # 3. Estado de los proyectos
                    st.subheader("3. Estado Actual de los Proyectos")
                    fig_pie = px.pie(
                        df_selection,
                        names="Estado_Actual",
                        title="Proporción por Estado del Proyecto",
                        hole=0.4
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
            except Exception as e_graph:
                st.error(f"Error al generar gráficos: {e_graph}")

            # --- MUESTRA DE DATOS ---
            with st.expander("Ver Datos Crudos"):
                st.dataframe(df_selection)

else:
    # Mensaje de bienvenida cuando no hay archivo
    st.info("👋 ¡Hola! Por favor sube un archivo CSV desde la barra lateral para comenzar el análisis.")
    
    # Opcional: Mostrar un ejemplo de cómo debe ser el archivo
    st.markdown("""
    **Formato esperado del CSV:**
    Debe contener columnas como: `Tecnologia`, `Operador`, `Capacidad_Instalada_MW`, `Estado_Actual`, etc.
    """)
