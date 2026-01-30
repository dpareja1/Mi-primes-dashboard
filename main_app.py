import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Dashboard Energía Renovable", layout="wide")

# Título
st.title("⚡ Análisis Exploratorio: Plantas de Energía Renovable")

# --- CARGA DE DATOS ---
@st.cache_data
def load_data():
    # Cargar el archivo CSV
    df = pd.read_csv("energia_renovable.csv")
    
    # Limpieza básica: Convertir fecha a datetime
    if 'Fecha_Entrada_Operacion' in df.columns:
        df['Fecha_Entrada_Operacion'] = pd.to_datetime(df['Fecha_Entrada_Operacion'])
    
    return df

try:
    df = load_data()
    st.success("Dataset cargado correctamente.")
except FileNotFoundError:
    st.error("Por favor asegúrate de que 'energia_renovable.csv' esté en la misma carpeta.")
    st.stop()

# --- SIDEBAR (FILTROS) ---
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
df_selection = df.query(
    "Tecnologia == @tecnologias & Estado_Actual == @estados"
)

# --- KPIs PRINCIPALES ---
st.markdown("### Métricas Generales")
col1, col2, col3, col4 = st.columns(4)

total_capacidad = df_selection["Capacidad_Instalada_MW"].sum()
promedio_eficiencia = df_selection["Eficiencia_Planta_Pct"].mean()
total_inversion = df_selection["Inversion_Inicial_MUSD"].sum()
conteo_plantas = df_selection.shape[0]

col1.metric("Capacidad Total (MW)", f"{total_capacidad:,.2f}")
col2.metric("Eficiencia Promedio", f"{promedio_eficiencia:.1f}%")
col3.metric("Inversión Total (MUSD)", f"${total_inversion:,.2f}")
col4.metric("Total Plantas", conteo_plantas)

st.markdown("---")

# --- VISUALIZACIONES ---

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
    st.subheader("2. Inversión vs. Generación Diaria")
    fig_scatter = px.scatter(
        df_selection,
        x="Inversion_Inicial_MUSD",
        y="Generacion_Diaria_MWh",
        color="Tecnologia",
        size="Capacidad_Instalada_MW",
        hover_data=["ID_Proyecto"],
        title="Relación Costo-Beneficio (Tamaño = Capacidad MW)"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

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

# --- MUESTRA DE DATOS ---
with st.expander("Ver Datos Crudos"):
    st.dataframe(df_selection)