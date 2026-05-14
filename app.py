import dash
from dash import dcc, html, dash_table
import plotly.express as px
import pandas as pd
import json

# Inicialización de la aplicación Dash
app = dash.Dash(__name__, title="Mortalidad en Colombia")

# Cargar los datos
# Nota: pd.read_csv puede tardar un momento dependiendo del tamaño del archivo.
df = pd.read_csv('data/datos.csv', sep=';', encoding='utf-8', low_memory=False)

# Mapear valores de Sexo si están codificados numéricamente (asumiendo 1: Masculino, 2: Femenino)
if df['SEXO'].dtype in [int, float, 'int64', 'float64']:
    df['Sexo_Label'] = df['SEXO'].map({1: 'Masculino', 2: 'Femenino'}).fillna('Desconocido')
else:
    df['Sexo_Label'] = df['SEXO']

# Cargar GeoJSON de Colombia
with open('data/Colombia.geo.json', encoding='utf-8') as f:
    colombia_geojson = json.load(f)

# --- CREACIÓN DE GRÁFICAS ---

# 1. Mapa: Distribución total de muertes por departamento
df_map = df.groupby('DEPARTAMENTO').size().reset_index(name='Muertes')
fig_map = px.choropleth_mapbox(
    df_map, 
    geojson=colombia_geojson, 
    locations='DEPARTAMENTO', 
    featureidkey='properties.NOMBRE_DPT',
    color='Muertes',
    mapbox_style="carto-positron",
    zoom=4, center={"lat": 4.5709, "lon": -74.2973},
    title="Distribución Total de Muertes por Departamento (2019)"
)
fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

# 2. Gráfico de líneas: Total de muertes por mes
df_mes = df.groupby('MES').size().reset_index(name='Muertes').sort_values('MES')
fig_line = px.line(df_mes, x='MES', y='Muertes', markers=True, title="Total de Muertes por Mes")

# 3. Gráfico de barras: 5 ciudades más violentas (homicidios código X95)
df_homicidios = df[df['COD_MUERTE'].astype(str).str.startswith('X95', na=False)]
df_violent = df_homicidios.groupby('MUNICIPIO').size().reset_index(name='Homicidios').sort_values('Homicidios', ascending=False).head(5)
fig_bar_ciudades = px.bar(df_violent, x='MUNICIPIO', y='Homicidios', title="Top 5 Ciudades Más Violentas (Homicidios X95)")

# 4. Gráfico circular: 10 ciudades con menor índice de mortalidad (valores absolutos)
df_ciudades_min = df.groupby('MUNICIPIO').size().reset_index(name='Muertes').sort_values('Muertes', ascending=True).head(10)
fig_pie = px.pie(df_ciudades_min, names='MUNICIPIO', values='Muertes', title="10 Ciudades con Menor Mortalidad")

# 5. Tabla: 10 principales causas de muerte
df_causas = df.groupby(['COD_MUERTE', 'DES3_MUERTE']).size().reset_index(name='Total Casos').sort_values('Total Casos', ascending=False).head(10)
# Modificar el dataframe para mostrarlo en dash_table
df_causas.rename(columns={'COD_MUERTE': 'Código', 'DES3_MUERTE': 'Descripción de la Causa'}, inplace=True)

# 6. Gráfico de barras apiladas: Muertes por sexo en cada departamento
df_sexo_depto = df.groupby(['DEPARTAMENTO', 'Sexo_Label']).size().reset_index(name='Muertes')
fig_stack = px.bar(df_sexo_depto, x='DEPARTAMENTO', y='Muertes', color='Sexo_Label', title="Muertes por Sexo y Departamento", barmode='stack')

# 7. Histograma: Distribución de muertes por grupo de edad
fig_hist = px.histogram(df, x='GRUPO_EDAD1', title="Distribución de Muertes por Grupo de Edad")
fig_hist.update_layout(xaxis={'categoryorder':'total descending'})

# --- LAYOUT DE LA APLICACIÓN ---

app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'}, children=[
    html.H1("Actividad 4: Aplicación web interactiva para el análisis de mortalidad en Colombia", 
            style={'textAlign': 'center', 'color': '#2C3E50'}),
    html.H3("Autor: Johnathan Morales Vargas", 
            style={'textAlign': 'center', 'color': '#7F8C8D'}),
    html.Hr(),
    
    html.Div([
        html.Div([dcc.Graph(figure=fig_map)], style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(figure=fig_line)], style={'width': '50%', 'display': 'inline-block'}),
    ]),
    
    html.Div([
        html.Div([dcc.Graph(figure=fig_bar_ciudades)], style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(figure=fig_pie)], style={'width': '50%', 'display': 'inline-block'}),
    ]),
    
    html.Div([
        html.H3("Top 10 Principales Causas de Muerte"),
        dash_table.DataTable(
            data=df_causas.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df_causas.columns],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '5px'},
            style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'}
        )
    ], style={'padding': '20px'}),
    
    html.Div([dcc.Graph(figure=fig_stack)]),
    
    html.Div([dcc.Graph(figure=fig_hist)])
])

if __name__ == '__main__':
    app.run_server(debug=True)
