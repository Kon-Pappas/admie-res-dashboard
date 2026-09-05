import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
import io

# 1. Ημερομηνία αναφοράς (Χθεσινή μέρα)
date_target = datetime.now() - timedelta(days=1)
year = date_target.strftime('%Y')
month = date_target.strftime('%m')
yyyymmdd = date_target.strftime('%Y%m%d')
report_date = date_target.strftime('%d.%m.%Y')

print(f"Απευθείας ανάκτηση για ημερομηνία: {report_date}")

# Κατασκευή των URLs βάσει του μονοπατιού που ανακαλύψαμε
scada_url = f"https://www.admie.gr/sites/default/files/attached-files/type-file/{year}/{month}/{yyyymmdd}_SystemRealizationSCADA_01.xls"
mv_url = f"https://www.admie.gr/sites/default/files/attached-files/type-file/{year}/{month}/{yyyymmdd}_RESMV_01.xls"

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch_and_parse():
    try:
        print(f"Λήψη SCADA: {scada_url}")
        res_scada = requests.get(scada_url, headers=headers)
        
        print(f"Λήψη MV Injections: {mv_url}")
        res_mv = requests.get(mv_url, headers=headers)
        
        if res_scada.status_code != 200 or res_mv.status_code != 200:
            raise Exception("Τα αρχεία δεν έχουν ανέβει ακόμα στον server για αυτή την ημερομηνία.")

        # Ανάλυση Δεδομένων (Data Parsing)
        scada_df = pd.read_excel(io.BytesIO(res_scada.content), skiprows=4)
        mv_df = pd.read_excel(io.BytesIO(res_mv.content), skiprows=4)
        
        scada_cols = [str(c).lower() for c in scada_df.columns]
        scada_df.columns = scada_cols
        
        mv_cols = [str(c).lower() for c in mv_df.columns]
        mv_df.columns = mv_cols

        plot_df = pd.DataFrame({'Hour': range(1, 25)})

        # -- MV Injections (Β2, Γ2, Ε2, Στ2) --
        plot_df['PV_MV'] = mv_df['φβ'] if 'φβ' in mv_cols else 0
        plot_df['CHP_MV'] = mv_df['σηθυα'] if 'σηθυα' in mv_cols else 0
        plot_df['Small_Hydro_MV'] = mv_df['μυης'] if 'μυης' in mv_cols else 0
        plot_df['Biomass_MV'] = mv_df['β/α'] if 'β/α' in mv_cols else 0

        # -- SCADA (Β1, Γ1, Δ, Ε1, Στ1) --
        pv_cols = [c for c in scada_cols if 'pv' in c or 'pv2' in c]
        plot_df['PV_SCADA'] = scada_df[pv_cols].sum(axis=1) if pv_cols else 0

        cg_cols = [c for c in scada_cols if 'cg' in c]
        plot_df['CHP_SCADA'] = scada_df[cg_cols].sum(axis=1) if cg_cols else 0

        hydro_cols = [c for c in scada_cols if 'hydro' in c]
        small_hydro_cols = [c for c in hydro_cols if 'small' in c or '<5' in c]
        big_hydro_cols = [c for c in hydro_cols if c not in small_hydro_cols]
        plot_df['Hydro_SCADA'] = scada_df[big_hydro_cols].sum(axis=1) if big_hydro_cols else 0
        plot_df['Small_Hydro_SCADA'] = scada_df[small_hydro_cols].sum(axis=1) if small_hydro_cols else 0

        bm_cols = [c for c in scada_cols if 'bm' in c]
        plot_df['Biomass_SCADA'] = scada_df[bm_cols].sum(axis=1) if bm_cols else 0

        # -- SCADA (Α. Αιολικά - Αποκλεισμός άλλων) --
        exclude_keywords = ['pv', 'pv2', 'cg', 'hydro', 'bm', 'pump', 'bess', 'hour', 'ώρα', 'σύνολο', 'total', 'lignite', 'gas', 'thermal', 'net']
        wind_cols = [c for c in scada_cols if not any(kw in c for kw in exclude_keywords)]
        plot_df['Wind_SCADA'] = scada_df[wind_cols].sum(axis=1) if wind_cols else 0

        # -- ΤΕΛΙΚΑ ΑΘΡΟΙΣΜΑΤΑ --
        plot_df['Total_PV'] = plot_df['PV_SCADA'] + plot_df['PV_MV']
        plot_df['Total_CHP'] = plot_df['CHP_SCADA'] + plot_df['CHP_MV']
        plot_df['Total_Small_Hydro'] = plot_df['Small_Hydro_SCADA'] + plot_df['Small_Hydro_MV']
        plot_df['Total_Biomass'] = plot_df['Biomass_SCADA'] + plot_df['Biomass_MV']

        return plot_df, False, report_date

    except Exception as e:
        print(f"Σφάλμα: {e}")
        return generate_dummy_data(), True, report_date

def generate_dummy_data():
    return pd.DataFrame({
        'Hour': range(1, 25),
        'Wind_SCADA': [50] * 24,
        'Total_PV': [0,0,0,0,0,0,10,30,50,80,100,120,120,100,80,50,30,10,0,0,0,0,0,0],
        'Total_CHP': [20] * 24,
        'Hydro_SCADA': [10] * 24,
        'Total_Small_Hydro': [5] * 24,
        'Total_Biomass': [2] * 24
    })

plot_df, is_dummy, report_date = fetch_and_parse()
title_status = "ΠΡΟΣΟΜΟΙΩΣΗ (Αναμονή δημοσίευσης από ΑΔΜΗΕ)" if is_dummy else "ΠΡΑΓΜΑΤΙΚΑ ΔΕΔΟΜΕΝΑ"

fig = px.bar(plot_df, 
             x='Hour', 
             y=['Total_Biomass', 'Total_Small_Hydro', 'Hydro_SCADA', 'Total_CHP', 'Total_PV', 'Wind_SCADA'],
             title=f'Ημερήσια Παραγωγή ΑΠΕ (MWh) - Ημερομηνία: {report_date} [{title_status}]',
             labels={'value': 'Παραγωγή (MWh)', 'variable': 'Τεχνολογία', 'Hour': 'Ώρα'},
             barmode='stack',
             color_discrete_sequence=px.colors.qualitative.Set2)

fig.update_xaxes(tickmode='linear', tick0=1, dtick=1)
fig.write_html("index.html")
print("Ολοκληρώθηκε.")
