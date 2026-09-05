import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
import io
import os

# 1. Ημερομηνία αναφοράς (Χθεσινή μέρα)
date_target = datetime.now() - timedelta(days=1)
date_formatted = date_target.strftime('%Y-%m-%d')
date_str = date_target.strftime('%Y-%m-%d')

print(f"Λήψη δεδομένων ΑΔΜΗΕ μέσω API για: {date_formatted}")

csv_filename = "historical_data.csv"

# Τα επίσημα URLs του API του ΑΔΜΗΕ
scada_url = f"https://www.admie.gr/getOperationMarketFile?dateStart={date_formatted}&dateEnd={date_formatted}&FileCategory=SystemRealizationSCADA"
mv_url = f"https://www.admie.gr/getOperationMarketFile?dateStart={date_formatted}&dateEnd={date_formatted}&FileCategory=RESMV"

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch_real_data():
    try:
        res_scada = requests.get(scada_url, headers=headers)
        res_mv = requests.get(mv_url, headers=headers)
        
        print(f"SCADA Status: {res_scada.status_code}, MV Status: {res_mv.status_code}")
        
        if res_scada.status_code != 200 or res_mv.status_code != 200:
            raise Exception(f"API Error - SCADA: {res_scada.status_code}, MV: {res_mv.status_code}")

        # Ανάγνωση με δοκιμή και των δύο engines για απόλυτη ασφάλεια (.xls / .xlsx)
        try:
            scada_df = pd.read_excel(io.BytesIO(res_scada.content), skiprows=4, engine='xlrd')
        except:
            scada_df = pd.read_excel(io.BytesIO(res_scada.content), skiprows=4, engine='openpyxl')
            
        try:
            mv_df = pd.read_excel(io.BytesIO(res_mv.content), skiprows=4, engine='xlrd')
        except:
            mv_df = pd.read_excel(io.BytesIO(res_mv.content), skiprows=4, engine='openpyxl')
        
        scada_cols = [str(c).lower() for c in scada_df.columns]
        scada_df.columns = scada_cols
        mv_cols = [str(c).lower() for c in mv_df.columns]
        mv_df.columns = mv_cols

        plot_df = pd.DataFrame({'Hour': range(1, 25)})

        # Εφαρμογή των κανόνων σου
        plot_df['PV_MV'] = mv_df['φβ'] if 'φβ' in mv_cols else 0
        plot_df['CHP_MV'] = mv_df['σηθυα'] if 'σηθυα' in mv_cols else 0
        plot_df['Small_Hydro_MV'] = mv_df['μυης'] if 'μυης' in mv_cols else 0
        plot_df['Biomass_MV'] = mv_df['β/α'] if 'β/α' in mv_cols else 0

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

        exclude_keywords = ['pv', 'pv2', 'cg', 'hydro', 'bm', 'pump', 'bess', 'hour', 'ώρα', 'σύνολο', 'total', 'lignite', 'gas', 'thermal', 'net']
        wind_cols = [c for c in scada_cols if not any(kw in c for kw in exclude_keywords)]
        plot_df['Wind_SCADA'] = scada_df[wind_cols].sum(axis=1) if wind_cols else 0

        plot_df['Total_PV'] = plot_df['PV_SCADA'] + plot_df['PV_MV']
        plot_df['Total_CHP'] = plot_df['CHP_SCADA'] + plot_df['CHP_MV']
        plot_df['Total_Small_Hydro'] = plot_df['Small_Hydro_SCADA'] + plot_df['Small_Hydro_MV']
        plot_df['Total_Biomass'] = plot_df['Biomass_SCADA'] + plot_df['Biomass_MV']

        plot_df['Date'] = date_str
        return plot_df, False
    except Exception as e:
        print(f"Σφάλμα λήψης μέσω API: {e}")
        hours = list(range(1, 25))
        dummy_df = pd.DataFrame({
            'Date': [date_str] * 24,
            'Hour': hours,
            'Wind_SCADA': [70] * 24,
            'Total_PV': [0,0,0,0,0,0,20,50,90,120,150,180,180,150,120,90,50,20,0,0,0,0,0,0],
            'Total_CHP': [20] * 24,
            'Hydro_SCADA': [15] * 24,
            'Total_Small_Hydro': [8] * 24,
            'Total_Biomass': [3] * 24
        })
        return dummy_df, True

# Λήψη δεδομένων
today_df, is_dummy = fetch_real_data()

# Ενημέρωση Historical CSV
if os.path.exists(csv_filename):
    history_df = pd.read_csv(csv_filename)
    history_df = history_df[history_df['Date'] != date_str]
    full_df = pd.concat([history_df, today_df], ignore_index=True)
else:
    full_df = today_df

full_df.to_csv(csv_filename, index=False)

# Δημιουργία Γραφήματος
status_text = "ΠΡΟΣΟΜΟΙΩΣΗ (Αναμονή δημοσίευσης)" if is_dummy else "ΠΡΑΓΜΑΤΙΚΑ ΔΕΔΟΜΕΝΑ ΑΔΜΗΕ"

fig = px.bar(today_df, 
             x='Hour', 
             y=['Total_Biomass', 'Total_Small_Hydro', 'Hydro_SCADA', 'Total_CHP', 'Total_PV', 'Wind_SCADA'],
             title=f'Ημερήσια Παραγωγή ΑΠΕ (MWh) - {date_str} [{status_text}]',
             labels={'value': 'Παραγωγή (MWh)', 'variable': 'Τεχνολογία', 'Hour': 'Ώρα'},
             barmode='stack',
             color_discrete_sequence=px.colors.qualitative.Set2)

fig.update_xaxes(tickmode='linear', tick0=1, dtick=1)
fig.write_html("index.html")
print("Η διαδικασία ολοκληρώθηκε!")
