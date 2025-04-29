import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Dashboard de Delitos", page_icon="🚨", layout="wide")

# Título del dashboard
st.title('Dashboard de Delitos en Buenos Aires 🚨')
st.markdown("Análisis de datos de delitos entre 2016-2023")

# Leer CSV con manejo mejorado de comunas
@st.cache_data
def cargar_datos():

    
    df = pd.read_csv("datasets_delitos_2019_2023_limpio.csv")
    df = df.convert_dtypes()
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

    return df

df = cargar_datos()

# Sidebar para filtros
st.sidebar.header("Filtros")

# Filtro por año
años = sorted(df['anio'].unique())
año_seleccionado = st.sidebar.multiselect(
    "Seleccionar Año:",
    options=años,
    default=años[-1]  # Último año por defecto
)

# Filtro por tipo de delito
tipos_delito = sorted(df['tipo'].unique())
tipo_seleccionado = st.sidebar.multiselect(
    "Tipo de Delito:",
    options=tipos_delito,
    default=tipos_delito[:3]  # Primeros 3 tipos por defecto
)

# Filtro por día de la semana
dias = ['Laboral', 'Fin de semana']
dia_seleccionado = st.sidebar.multiselect(
    "Tipo de Día:",
    options=dias,
    default=dias
)

# Aplicar filtros
df_filtrado = df.copy()
if año_seleccionado:
    df_filtrado = df_filtrado[df_filtrado['anio'].isin(año_seleccionado)]
if tipo_seleccionado:
    df_filtrado = df_filtrado[df_filtrado['tipo'].isin(tipo_seleccionado)]
if dia_seleccionado:
    df_filtrado = df_filtrado[df_filtrado['tipo_dia'].isin(dia_seleccionado)]

# Métricas principales
st.header("Métricas Principales")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_delitos = len(df_filtrado)
    st.metric("Total Delitos", f"{total_delitos:,}")

with col2:
    delitos_con_arma = df_filtrado[df_filtrado['uso_arma'] == 'SI'].shape[0]
    porcentaje_arma = (delitos_con_arma / total_delitos * 100) if total_delitos > 0 else 0
    st.metric("Uso de Armas", f"{porcentaje_arma:.1f}%")

with col3:
    delitos_con_moto = df_filtrado[df_filtrado['uso_moto'] == 'SI'].shape[0]
    porcentaje_moto = (delitos_con_moto / total_delitos * 100) if total_delitos > 0 else 0
    st.metric("Uso de Motos", f"{porcentaje_moto:.1f}%")

with col4:
    # Excluir "Sin datos" del conteo de comunas
    comunas_afectadas = df_filtrado[df_filtrado['comuna'] != 0]['comuna'].nunique()
    st.metric("Comunas Afectadas", comunas_afectadas)

# Gráficos
st.header("Análisis de Delitos")

# Gráfico 1: Delitos por tipo (horizontal bar chart)
st.subheader("Delitos por Tipo")
delitos_por_tipo = df_filtrado.groupby('tipo').size().reset_index(name='cantidad')
delitos_por_tipo = delitos_por_tipo.sort_values('cantidad', ascending=True)

fig_tipos = px.bar(
    delitos_por_tipo,
    y='tipo',
    x='cantidad',
    orientation='h',
    color='cantidad',
    color_continuous_scale='Reds',
    title='Cantidad de Delitos por Tipo'
)
fig_tipos.update_layout(height=400)
st.plotly_chart(fig_tipos, use_container_width=True)

# Layout de dos columnas
col1, col2 = st.columns(2)

# Gráfico 2: Delitos por año
with col1:
    delitos_por_año = df_filtrado.groupby('anio').size().reset_index(name='cantidad')
    fig_años = px.line(
        delitos_por_año, 
        x='anio', 
        y='cantidad',
        markers=True,
        title='Evolución de Delitos por Año',
        color_discrete_sequence=['crimson']
    )
    fig_años.update_layout(height=400)
    st.plotly_chart(fig_años, use_container_width=True)

# Gráfico 3: Delitos por tipo de día
with col2:
    delitos_por_dia = df_filtrado.groupby('tipo_dia').size().reset_index(name='cantidad')
    fig_dias = px.pie(
        delitos_por_dia,
        values='cantidad',
        names='tipo_dia',
        hole=0.4,
        title='Distribución por Tipo de Día',
        color_discrete_sequence=['#FF9999', '#66B2FF']
    )
    fig_dias.update_layout(height=400)
    st.plotly_chart(fig_dias, use_container_width=True)

# Gráfico 4: Mapa de calor por franja horaria y día de la semana
st.subheader("Patrones Temporales")
# Asegurar que día de semana y franja horaria son numéricos para el heatmap
df_heatmap = df_filtrado.copy()
df_heatmap['dia_semana_num'] = pd.to_numeric(df_heatmap['dia_semana_num'], errors='coerce')

# Crear heatmap de delitos por día de la semana y hora
heatmap_data = df_heatmap.groupby(['dia_semana_num', 'franja']).size().reset_index(name='cantidad')
heatmap_pivot = heatmap_data.pivot_table(
    values='cantidad', 
    index='franja', 
    columns='dia_semana_num', 
    fill_value=0
)

# Mapeo para etiquetas de días
dias_semana = {0: 'Lun', 1: 'Mar', 2: 'Mié', 3: 'Jue', 4: 'Vie', 5: 'Sáb', 6: 'Dom'}
nuevas_columnas = [dias_semana.get(col, col) for col in heatmap_pivot.columns]
heatmap_pivot.columns = nuevas_columnas

fig_heatmap = px.imshow(
    heatmap_pivot,
    labels={'y': 'Hora del día', 'x': 'Día de la semana', 'color': 'Cantidad de delitos'},
    color_continuous_scale="Reds",
    title="Mapa de calor: Delitos por día de la semana y hora"
)
fig_heatmap.update_layout(height=500)
st.plotly_chart(fig_heatmap, use_container_width=True)

# Gráfico 5: Mapa de delitos
st.header("Mapa de Delitos")

#     # 4. Preparar datos para el mapa coroplético
try:
    # Agrupar delitos por barrio para el mapa
    delitos_por_barrio = df_filtrado.groupby('barrio').size().reset_index(name='cantidad')
    
    # Cargar GeoJSON con los límites de los barrios de Buenos Aires
    import requests
    
    # URL del GeoJSON de barrios de Buenos Aires
    url_geojson = "https://cdn.buenosaires.gob.ar/datosabiertos/datasets/ministerio-de-educacion/barrios/barrios.geojson"
    
    # Descargar el GeoJSON
    response = requests.get(url_geojson)
    barrios_geojson = response.json()
    
    # Examinar la estructura del GeoJSON para asegurar compatibilidad
    # Identificar la propiedad que contiene los nombres de barrios
    properties_keys = barrios_geojson['features'][0]['properties'].keys()
    
    # Buscar la clave más apropiada para los nombres de barrios
    barrio_key = next((k for k in properties_keys if 'barrio' in k.lower() or 'nombre' in k.lower()), None)
    if not barrio_key:
        barrio_key = list(properties_keys)[0]  # Usar la primera propiedad si no se encuentra una específica
    
    # Mostrar los primeros barrios del GeoJSON para verificar
    barrios_en_geojson = [feature['properties'][barrio_key] for feature in barrios_geojson['features'][:5]]
    
    # Ajustar el GeoJSON para que coincida con los nombres de barrios
    for feature in barrios_geojson['features']:
        feature['id'] = feature['properties'][barrio_key].upper()  # Convertir a mayúsculas para coincidir
    
    
    # Ahora verificamos si tenemos datos para mostrar después de todos los intentos de coincidencia
    if len(delitos_por_barrio) > 0:
        # Crear el mapa coroplético
        fig_mapa = px.choropleth_mapbox(
            delitos_por_barrio,
            geojson=barrios_geojson,
            locations='barrio',  # Usar la versión normalizada
            featureidkey='id',
            color='cantidad',
            color_continuous_scale="Reds",
            mapbox_style="carto-positron",
            zoom=9.5,
            center={"lat": -34.6, "lon": -58.4},
            opacity=0.7,
            title="Mapa Coroplético: Delitos por Barrio"
        )
        
        # Centrar en Buenos Aires
        fig_mapa.update_layout(
            mapbox=dict(
                center=dict(lat=-34.6, lon=-58.4),
                zoom=10
            ),
            height=600
        )
        
        st.plotly_chart(fig_mapa, use_container_width=True)
        
        # Información adicional sobre los datos mostrados en el mapa
        st.info(f"El mapa muestra {delitos_por_barrio['cantidad'].sum():,} delitos distribuidos en {len(delitos_por_barrio)} barrios.")
    else:
        st.error("No se pudieron mapear los barrios. Mostrando mapa alternativo.")
        raise Exception("Sin coincidencias de barrios para el mapa coroplético")
        
except Exception as e:
    st.error(f"Error al crear el mapa coroplético: {str(e)}")
    
    
# Análisis por comunas
st.header("Análisis por Comuna")
# Filtrar comunas con delitos y agrupar por comuna
df_comunas_filtrado = df_filtrado[df_filtrado['comuna'] != 0]
delitos_por_comuna = df_comunas_filtrado.groupby('comuna').size().reset_index(name='cantidad')

# Ordenar de mayor a menor y seleccionar las 10 comunas con más delitos
delitos_por_comuna = delitos_por_comuna.sort_values('cantidad', ascending=False).head(10)

# Gráfico de barras para las Top 10 comunas
fig_comunas = px.bar(
    delitos_por_comuna,
    x='comuna',  # Usar comuna
    y='cantidad',
    color='cantidad',
    color_continuous_scale='Reds',
    title='Top 10 Comunas con Mayor Número de Delitos',
    labels={"comuna": "Comuna", "cantidad": "Cantidad de Delitos"}
)

# Configurar el diseño del gráfico
fig_comunas.update_layout(
    xaxis=dict(title="Comuna", tickprefix="Comuna "),
    yaxis=dict(title="Cantidad de Delitos"),
    height=500
)

# Mostrar el gráfico
st.plotly_chart(fig_comunas, use_container_width=True)

# Pie chart para tipos de delito por comuna seleccionada
col1, col2 = st.columns(2)

with col1:
    # Permitir seleccionar una comuna
    comunas_lista = sorted([c for c in df_filtrado['comuna'].unique() if c != 0])
    if comunas_lista:
        comuna_seleccionada = st.selectbox("Selecciona una comuna para analizar:", comunas_lista)
        
        # Filtrar por la comuna seleccionada
        df_comuna = df_filtrado[df_filtrado['comuna'] == comuna_seleccionada]
        
        # Gráfico de delitos por tipo en la comuna seleccionada
        delitos_comuna_tipo = df_comuna.groupby('tipo').size().reset_index(name='cantidad')
        
        fig_comuna_tipo = px.pie(
            delitos_comuna_tipo,
            values='cantidad',
            names='tipo',
            title=f'Tipos de Delito en Comuna {comuna_seleccionada}'
        )
        st.plotly_chart(fig_comuna_tipo, use_container_width=True)

with col2:
    # Evolución temporal para la comuna seleccionada
    if 'comuna_seleccionada' in locals() and not df_comuna.empty:
        df_comuna['mes_año'] = df_comuna['fecha'].dt.strftime('%Y-%m')
        delitos_comuna_tiempo = df_comuna.groupby('mes_año').size().reset_index(name='cantidad')
        
        fig_comuna_tiempo = px.line(
            delitos_comuna_tiempo,
            x='mes_año',
            y='cantidad',
            markers=True,
            title=f'Evolución Temporal de Delitos en Comuna {comuna_seleccionada}'
        )
        st.plotly_chart(fig_comuna_tiempo, use_container_width=True)

# Análisis Bidireccional Comuna - Barrio
st.header("Relación Comuna - Barrio")

# Crear tabs para navegar entre las dos vistas
tab_comuna, tab_barrio = st.tabs(["Explorar por Comuna", "Explorar por Barrio"])

# Tab 1: Explorar por Comuna
with tab_comuna:
    # Seleccionar comuna - usar comuna (excluyendo "Sin datos")
    comunas_lista = sorted([c for c in df_filtrado['comuna'].unique() if c != 0])
    if comunas_lista:
        comuna_seleccionada_tab = st.selectbox(
            "Selecciona una comuna:", 
            comunas_lista,
            key="comuna_tab"
        )
        
        # Obtener barrios de la comuna seleccionada - asegurar comparación correcta
        barrios_comuna = df_filtrado[df_filtrado['comuna'] == comuna_seleccionada_tab]['barrio'].unique()
        
        # Mostrar lista de barrios en esta comuna
        st.subheader(f"Barrios en Comuna {comuna_seleccionada_tab}")
        
        # Contar delitos por barrio en esta comuna - usar comuna
        barrios_delitos = df_filtrado[(df_filtrado['comuna'] == comuna_seleccionada_tab)].groupby('barrio').size().reset_index(name='cantidad')
        

        barrios_delitos = barrios_delitos.sort_values('cantidad', ascending=False)
        
        # Gráfico de barras horizontal para los barrios
        fig_barrios = px.bar(
            barrios_delitos,
            y='barrio',
            x='cantidad',
            orientation='h',
            color='cantidad',
            color_continuous_scale='Blues',
            title=f'Distribución de Delitos por Barrio en Comuna {comuna_seleccionada_tab}'
        )
        # fig_barrios.update_layout(height=min(600, len(barrios_comuna) * 30 + 200))
        st.plotly_chart(fig_barrios, use_container_width=True)
        
        # Tabla con información adicional (opcional)
        with st.expander("Ver tabla detallada de barrios"):
            st.write(barrios_delitos)

# Tab 2: Explorar por Barrio
with tab_barrio:
    # Filtrar por barrio
    barrios_lista = sorted([b for b in df_filtrado['barrio'].unique() if b != "Sin datos"])
    if barrios_lista:
        barrio_seleccionado = st.selectbox(
            "Selecciona un barrio:", 
            barrios_lista
        )
        
       # Obtener comuna(s) del barrio seleccionado - filtrar "Sin datos"
        comunas_barrio = df_filtrado[(df_filtrado['barrio'] == barrio_seleccionado)]

        
        comuna_counts = df_filtrado[(df_filtrado['barrio'] == barrio_seleccionado) & 
                                     (df_filtrado['comuna'] != 'Sin datos')]['comuna'].value_counts()
        comuna_principal = comuna_counts.idxmax()  # Comuna con más registros
            
            # Definir comuna_barrio como la más frecuente
        comuna_barrio = comuna_principal
            
            
        st.subheader(f"El barrio {barrio_seleccionado} pertenece a la Comuna {comuna_barrio}")
       
        
        # Análisis de delitos en este barrio
        df_barrio = df_filtrado[df_filtrado['barrio'] == barrio_seleccionado]
        
        # Crear visualizaciones para el barrio
        col1, col2 = st.columns(2)
        
        with col1:
            # Tipos de delito en el barrio
            tipos_barrio = df_barrio.groupby('tipo').size().reset_index(name='cantidad')
            tipos_barrio = tipos_barrio.sort_values('cantidad', ascending=False)
            
            fig_tipos_barrio = px.bar(
                tipos_barrio,
                x='tipo',
                y='cantidad',
                color='cantidad',
                color_continuous_scale='Greens',
                title=f'Tipos de Delito en el Barrio {barrio_seleccionado}'
            )
            st.plotly_chart(fig_tipos_barrio, use_container_width=True)
            
        with col2:
            # Evolución temporal de delitos en el barrio
            df_barrio['mes_año'] = df_barrio['fecha'].dt.strftime('%Y-%m')
            delitos_barrio_tiempo = df_barrio.groupby('mes_año').size().reset_index(name='cantidad')
            
            fig_barrio_tiempo = px.line(
                delitos_barrio_tiempo,
                x='mes_año',
                y='cantidad',
                markers=True,
                title=f'Evolución Temporal de Delitos en {barrio_seleccionado}',
                color_discrete_sequence=['green']
            )
            st.plotly_chart(fig_barrio_tiempo, use_container_width=True)
        
        # Comparativa con otros barrios de la misma comuna
        if comuna_barrio != "No disponible":
            st.subheader(f"Comparativa con otros barrios de la Comuna {comuna_barrio}")
            
            # Obtener todos los barrios de esta comuna - usar comuna para correcta comparación
            barrios_misma_comuna = df_filtrado[(df_filtrado['comuna'] == comuna_barrio)].groupby('barrio').size().reset_index(name='cantidad')
            barrios_misma_comuna = barrios_misma_comuna.sort_values('cantidad', ascending=False)
            
            # Resaltar el barrio seleccionado
            barrios_misma_comuna['color'] = barrios_misma_comuna['barrio'].apply(
                lambda x: '#1F77B4' if x != barrio_seleccionado else '#FF7F0E'
            )
            
            fig_comp_barrios = px.bar(
                barrios_misma_comuna,
                x='barrio',
                y='cantidad',
                color='barrio',
                title=f'Delitos en los Barrios de la Comuna {comuna_barrio}',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            # Resaltar el barrio seleccionado
            for i, bar in enumerate(fig_comp_barrios.data):
                if bar.name == barrio_seleccionado:
                    fig_comp_barrios.data[i].marker.color = 'red'
            
            st.plotly_chart(fig_comp_barrios, use_container_width=True)

# Nota al pie
st.markdown("---")
st.caption("Dashboard creado con Streamlit y Plotly Express. Datos de delitos 2019-2023.")


