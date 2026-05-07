import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# 1. Configuración de la Página
st.set_page_config(page_title="PGA Group - Indicadores", layout="wide")

# Colores Corporativos PGA
PGA_COLORS = {
    'pumpkin': '#ED7D31',
    'yellow': '#F9C035',
    'gray': '#595959',
    'platinum': '#D3D4D9'
}

LINE_COLORS = {
    'Inflacion BCV': '#D3D4D9',
    'Inf. Acum BCV': '#ED7D31',
    'Inflación Acumulada': '#ED7D31',
    'Tasa bcv': '#F9C035',
    'Deval. Acum BCV': '#595959',
    'Devaluación Acumulada BCV': '#F9C035',
    'Devaluación Acumulada USDT': '#595959'
}

# --- CARGA DE DATOS ---
@st.cache_data
def load_data():
    base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
    file_path = os.path.join(base_path, 'Indicadores_abril_2026.xlsx')
    
    if not os.path.exists(file_path):
        st.error(f"❌ No se encontró el archivo: {file_path}")
        st.stop()
        
    df = pd.read_excel(file_path, sheet_name='Data')
    df.columns = df.columns.str.strip()
    
    meses_dict = {
        'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
        'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
    }
    
    df['Año_Num'] = df['Año'].astype(int)
    df['Año'] = df['Año'].astype(int).astype(str)
    df['Mes_Num'] = df['Mes'].str.strip().str.upper().map(meses_dict)
    df['Fecha_DT'] = pd.to_datetime(df['Año_Num'].astype(str) + '-' + df['Mes_Num'].astype(str).str.zfill(2) + '-01')
    
    # Nombres abreviados para el histórico
    df['Inf. Acum BCV'] = df['Inflación acumulada BCV']
    df['Deval. Acum BCV'] = df['Devaluación acumulada BCV']
    
    # FILTRO: Solo 2025 en adelante
    df = df[df['Fecha_DT'] >= '2025-01-01'].copy()
    
    return df.sort_values('Fecha_DT')

df_2025 = load_data()

# --- FUNCIÓN DE GRÁFICO MAESTRA ---
def plot_pga_master(data, columns, title):
    if not columns: return
    fig, ax = plt.subplots(figsize=(11, 4))
    
    for col in columns:
        if col in data.columns:
            color = LINE_COLORS.get(col, '#D3D4D9')
            ax.plot(data['Fecha_DT'], data[col], marker='o', label=col, linewidth=2.5, color=color)
    
    ax.set_title(title, fontsize=12, color=PGA_COLORS['gray'], fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    
    # Ajuste dinámico de escala
    is_percent = any(c in str(columns) for c in ['Inflación', 'Devaluación', 'Acum', 'Inf'])
    if is_percent:
        vals = data[columns].values
        # Añadir un margen de 10% arriba y abajo para que la línea no toque los bordes
        ax.set_ylim(vals.min() - 0.01, vals.max() + 0.01)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1%}'))
    else:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'Bs. {x:,.2f}'))
    
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.legend(frameon=False, loc='upper left', fontsize=9)
    plt.xticks(rotation=45, fontsize=9)
    st.pyplot(fig)

# --- INTERFAZ ---
st.title("📊 Dashboard PGA Group")

# PARTE 1: HISTÓRICO
st.markdown(f"<div style='border-left:5px solid {PGA_COLORS['pumpkin']}; padding-left:10px;'><h3>1. Histórico de Mercado (Desde 2025)</h3></div>", unsafe_allow_html=True)
col_h1, col_h2, col_h3, col_h4 = st.columns(4)

h_inf = col_h1.checkbox("📉 Inf. Mes")
h_acum = col_h2.checkbox("📈 Inf. Acum")
h_deval = col_h3.checkbox("🏛️ Deval. Acum")
h_tasa = col_h4.checkbox("💰 Tasa BCV")

sel_h = []
if h_inf: sel_h.append('Inflacion BCV')
if h_acum: sel_h.append('Inf. Acum BCV')
if h_deval: sel_h.append('Deval. Acum BCV')
if h_tasa: sel_h.append('Tasa bcv')

if sel_h:
    formatos_h = {c: ('{:.2%}' if 'Tasa' not in c else 'Bs. {:,.2f}') for c in sel_h}
    st.dataframe(df_2025[['Año', 'Mes'] + sel_h].style.format(formatos_h), hide_index=True)
    plot_pga_master(df_2025, sel_h, "Evolución de Indicadores")

st.divider()

# PARTE 2: SIMULADOR
st.markdown(f"<div style='border-left:5px solid {PGA_COLORS['pumpkin']}; padding-left:10px;'><h3>2. Simulador de Acumulación Dinámica</h3></div>", unsafe_allow_html=True)

meses_dispo = df_2025['Fecha_DT'].dt.strftime('%Y-%m').unique()
m_base_str = st.selectbox("📅 Seleccione Mes Base:", meses_dispo)

col_s1, col_s2, col_s3 = st.columns(3)
s_inf = col_s1.checkbox("Inflación Acumulada", value=True)
s_bcv = col_s2.checkbox("Devaluación BCV")
s_usdt = col_s3.checkbox("Devaluación USDT")

sel_s = []
if s_inf: sel_s.append('Inflación Acumulada')
if s_bcv: sel_s.append('Devaluación Acumulada BCV')
if s_usdt: sel_s.append('Devaluación Acumulada USDT')

if sel_s:
    f_base = pd.to_datetime(m_base_str)
    df_d = df_2025[df_2025['Fecha_DT'] >= f_base].copy()
    
    # Localizar el cierre del mes anterior para que no empiece en 0
    # Si no hay mes anterior (porque es el inicio de la tabla), usamos el primer dato real
    idx_base = df_2025.index[df_2025['Fecha_DT'] == f_base].tolist()[0]
    
    # Inflación acumulada
    df_d['Inflación Acumulada'] = (1 + df_d['Inflacion BCV']).cumprod() - 1
    
    # Devaluación BCV calculada contra el mes inmediatamente anterior
    if idx_base > 0:
        t_ref_bcv = df_2025.loc[idx_base - 1, 'Tasa bcv']
    else:
        t_ref_bcv = df_d['Tasa bcv'].iloc[0] / (1 + 0.02) # Estimado si es el primer dato
    df_d['Devaluación Acumulada BCV'] = (df_d['Tasa bcv'] / t_ref_bcv) - 1
    
    # Devaluación USDT
    if 'Tasa Promedio USDT' in df_2025.columns:
        if idx_base > 0:
            t_ref_usdt = df_2025.loc[idx_base - 1, 'Tasa Promedio USDT']
        else:
            t_ref_usdt = df_d['Tasa Promedio USDT'].iloc[0] / 1.02
        df_d['Devaluación Acumulada USDT'] = (df_d['Tasa Promedio USDT'] / t_ref_usdt) - 1
    else:
        df_d['Devaluación Acumulada USDT'] = 0.0

    formatos_s = {c: "{:.2%}" for c in sel_s}
    st.dataframe(df_d[['Año', 'Mes'] + sel_s].style.format(formatos_s), hide_index=True)
    plot_pga_master(df_d, sel_s, f"Acumulación desde {m_base_str}")
    