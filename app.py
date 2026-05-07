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
    
    df['Año_Num'] = pd.to_numeric(df['Año'], errors='coerce')
    df = df.dropna(subset=['Año_Num', 'Mes'])
    df['Año_Num'] = df['Año_Num'].astype(int)
    df['Año'] = df['Año_Num'].astype(str)
    df['Mes_Num'] = df['Mes'].str.strip().str.upper().map(meses_dict)
    df = df.dropna(subset=['Mes_Num'])
    df['Mes_Num'] = df['Mes_Num'].astype(int)
    df['Fecha_DT'] = pd.to_datetime(df['Año_Num'].astype(str) + '-' + df['Mes_Num'].astype(str).str.zfill(2) + '-01')
    
    df['Inf. Acum BCV'] = df['Inflación acumulada BCV']
    df['Deval. Acum BCV'] = df['Devaluación acumulada BCV']
    
    if 'Tasa Promedio USDT' not in df.columns:
        if 'Tasa Enparalelo' in df.columns:
            df['Tasa Promedio USDT'] = df['Tasa Enparalelo']
        else:
            df['Tasa Promedio USDT'] = df['Tasa bcv'] * 1.1
    
    df = df.sort_values('Fecha_DT')
    df_2025 = df[df['Fecha_DT'] >= '2025-01-01'].copy()
    
    return df_2025

df_2025 = load_data()

# --- FUNCIÓN DE GRÁFICO ---
def plot_pga_master(data, columns, title):
    if not columns or data.empty:
        return
    
    fig, ax = plt.subplots(figsize=(11, 4))
    
    for col in columns:
        if col in data.columns and pd.api.types.is_numeric_dtype(data[col]):
            color = LINE_COLORS.get(col, '#D3D4D9')
            ax.plot(data['Fecha_DT'], data[col], marker='o', label=col, linewidth=2.5, color=color)
    
    ax.set_title(title, fontsize=12, color=PGA_COLORS['gray'], fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    
    is_percent = any(c in str(columns) for c in ['Inflación', 'Devaluación', 'Acum', 'Inf'])
    if is_percent:
        numeric_cols = [col for col in columns if col in data.columns and pd.api.types.is_numeric_dtype(data[col])]
        if numeric_cols:
            vals = data[numeric_cols].values
            if len(vals) > 0 and not pd.isna(vals).all():
                min_val = vals.min()
                max_val = vals.max()
                if not pd.isna(min_val) and not pd.isna(max_val):
                    margin = (max_val - min_val) * 0.1 if max_val != min_val else 0.1
                    ax.set_ylim(min_val - max(0.01, margin), max_val + max(0.01, margin))
                    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1%}'))
    
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.legend(frameon=False, loc='upper left', fontsize=9)
    plt.xticks(rotation=45, fontsize=9)
    st.pyplot(fig)

# --- INTERFAZ ---
st.title("📊 Dashboard PGA Group")

if df_2025.empty:
    st.error("No hay datos disponibles")
    st.stop()

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
    available_cols = [col for col in sel_h if col in df_2025.columns]
    if available_cols:
        formatos_h = {}
        for col in available_cols:
            if 'Tasa' in col and 'bcv' in col.lower():
                formatos_h[col] = 'Bs. {:,.2f}'
            else:
                formatos_h[col] = '{:.2%}'
        
        display_df = df_2025[['Año', 'Mes'] + available_cols].copy()
        st.dataframe(display_df.style.format(formatos_h), hide_index=True)
        plot_pga_master(df_2025, available_cols, "Evolución de Indicadores")

st.divider()

# --- PARTE 2: SIMULADOR (COMPLETAMENTE REWRITE) ---
st.markdown(f"<div style='border-left:5px solid {PGA_COLORS['pumpkin']}; padding-left:10px;'><h3>2. Simulador de Acumulación Dinámica</h3></div>", unsafe_allow_html=True)

# Obtener fechas únicas ordenadas
df_sorted = df_2025.sort_values('Fecha_DT')
unique_dates = df_sorted['Fecha_DT'].unique()
date_labels = [d.strftime('%Y-%m') for d in unique_dates]

if len(date_labels) > 0:
    selected_date_label = st.selectbox("📅 Seleccione Mes Base:", date_labels)
    selected_date = pd.to_datetime(selected_date_label)
    
    col_s1, col_s2, col_s3 = st.columns(3)
    s_inf = col_s1.checkbox("Inflación Acumulada", value=True)
    s_bcv = col_s2.checkbox("Devaluación BCV")
    s_usdt = col_s3.checkbox("Devaluación USDT")
    
    sel_s = []
    if s_inf: sel_s.append('Inflación Acumulada')
    if s_bcv: sel_s.append('Devaluación Acumulada BCV')
    if s_usdt: sel_s.append('Devaluación Acumulada USDT')
    
    if sel_s:
        # Filtrar desde la fecha seleccionada
        df_filtered = df_2025[df_2025['Fecha_DT'] >= selected_date].copy()
        
        if not df_filtered.empty:
            # Obtener valores de referencia del primer mes (mes base)
            first_row = df_filtered.iloc[0]
            ref_tasa_bcv = first_row['Tasa bcv']
            ref_tasa_usdt = first_row['Tasa Promedio USDT'] if 'Tasa Promedio USDT' in df_filtered.columns else 1
            
            # Calcular acumulados
            df_filtered['Inflación Acumulada'] = (1 + df_filtered['Inflacion BCV']).cumprod() - 1
            df_filtered['Devaluación Acumulada BCV'] = (df_filtered['Tasa bcv'] / ref_tasa_bcv) - 1
            
            if 'Tasa Promedio USDT' in df_filtered.columns:
                df_filtered['Devaluación Acumulada USDT'] = (df_filtered['Tasa Promedio USDT'] / ref_tasa_usdt) - 1
            else:
                df_filtered['Devaluación Acumulada USDT'] = 0.0
            
            # Mostrar solo columnas disponibles
            available_cols = [col for col in sel_s if col in df_filtered.columns]
            
            if available_cols:
                format_dict = {col: "{:.2%}" for col in available_cols}
                display_df = df_filtered[['Año', 'Mes'] + available_cols].copy()
                st.dataframe(display_df.style.format(format_dict), hide_index=True)
                plot_pga_master(df_filtered, available_cols, f"Acumulación desde {selected_date_label}")
            else:
                st.warning("No se encontraron las columnas seleccionadas")
        else:
            st.warning(f"No hay datos desde {selected_date_label}")
else:
    st.warning("No hay fechas disponibles")