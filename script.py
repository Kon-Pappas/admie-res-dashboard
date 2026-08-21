import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
import io

# 1. Βρίσκουμε την χθεσινή ημερομηνία
date_target = datetime.now() - timedelta(days=1)
date_str = date_target.strftime('%Y%m%d')

print(f"Αναζήτηση δεδομένων για: {date_str}")

# 2. URLs του ΑΔΜΗΕ (Πιθανή δομή. Αν αποτύχει, θα χρειαστούμε τη μέθοδο POST της φόρμας)
url_scada = f"https://www.admie.gr/get-file/Unit_Production_{date_str}.xls" 
url_mv = f"https://www.admie.gr/get-file/Actual_RES_MV_Injections_{date_str}.xls"

def fetch_and_parse():
    try:
        print("Προσπάθεια λήψης αρχείων...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        # Λήψη αρχείων
        res_scada = requests.get(url_scada, headers=headers)
        res_mv = requests.get(url_mv, headers=headers)
        
        if res_scada.status_code != 200 or res_mv.status_code != 200:
            raise Exception("Τα αρχεία δεν βρέθηκαν στο συγκεκριμένο URL.")

        # 3. Φόρτωση των δεδομένων απευθείας από τη μνήμη
        scada_df = pd.read_excel(io.BytesIO(res_scada.content), skiprows=4)
        mv_df = pd.read_excel(io.BytesIO(res_mv.content), skiprows=4)
        
        # Μετατροπή των τίτλων στηλών σε μικρά γράμματα για εύκολη αναζήτηση
        scada_cols = [str(c).lower() for c in scada_df.columns]
        scada_df.columns = scada_cols
        
        mv_cols = [str(c).lower() for c in mv_df.columns]
        mv_df.columns = mv_cols

        plot_df = pd.DataFrame({'Hour': range(1, 25)})

        # --- Β2. Γ2. Ε2. Στ2. MV Injections ---
        plot_df['PV_MV'] = mv_df['φβ'] if 'φβ' in mv_cols else 0
        plot_df['CHP_MV'] = mv_df['σηθυα'] if 'σηθυα' in mv_cols else 0
        plot_df['Small_Hydro_MV'] = mv_df['μυης'] if 'μυης' in mv_cols else 0
        plot_df['Biomass_MV'] = mv_df['β/α'] if 'β/α' in mv_cols else 0

        # --- Β1. Φωτοβολταϊκά (pv, pv2) SCADA ---
        pv_cols = [c for c in scada_cols if 'pv' in c or 'pv2' in c]
        plot_df['PV_SCADA'] = scada_df[pv_cols].sum(axis=1) if pv_cols else 0

        # --- Γ1. Συμπαραγωγή (cg) SCADA ---
        cg_cols = [c for c in scada_cols if 'cg' in c]
        plot_df['CHP_SCADA'] = scada_df[cg_cols].sum(axis=1) if cg_cols else 0

        # --- Δ. & Ε1. Hydro & Μικρά Υδροηλεκτρικά SCADA ---
        hydro_cols = [c for c in scada_cols if 'hydro' in c]
        # Ξεχωρίζουμε τα μικρά (Αν ο ΑΔΜΗΕ δεν τα έχει με όνομα 'small', θα θέλει λίστα ονομάτων εδώ)
        small_hydro_cols = [c for c in hydro_cols if 'small' in c or '<5' in c]
        big_hydro_cols = [c for c in hydro_cols if c not in small_hydro_cols]
        
        plot_df['Hydro_SCADA'] = scada_df[big_hydro_cols].sum(axis=1) if big_hydro_cols else 0
        plot_df['Small_Hydro_SCADA'] = scada_df[small_hydro_cols].sum(axis=1) if small_hydro_cols else 0

        # --- Στ1. Biomass (bm) SCADA ---
        bm_cols = [c for c in scada_cols if 'bm' in c]
        plot_df['Biomass_SCADA'] = scada_df[bm_cols].sum(axis=1) if bm_cols else 0

        # --- Α. Αιολικά (ό,τι δεν έχει ακρωνύμιο) SCADA ---
        # Φιλτράρουμε ρητά όλες τις άλλες τεχνολογίες και τα γενικά σύνολα.
        exclude_keywords = ['pv', 'pv2', 'cg', 'hydro', 'bm', 'pump', 'bess', 'hour', 'ώρα', 'σύνολο', 'total', 'lignite', 'gas', 'thermal']
        wind_cols = [c for c in scada_cols if not any(kw in c for kw in exclude_keywords)]
        plot_df['Wind_SCADA'] = scada_df[wind_cols].sum(axis=1) if wind_cols else 0

        # --- ΤΕΛΙΚΑ ΑΘΡΟΙΣΜΑΤΑ ΓΙΑ ΤΟ ΓΡΑΦΗΜΑ ---
        plot_df['Total_PV'] = plot_df['PV_SCADA'] + plot_df['PV_MV']
        plot_df['Total_CHP'] = plot_df['CHP_SCADA'] + plot_df['CHP_MV']
        plot_df['Total_Small_Hydro'] = plot_df['Small_Hydro_SCADA'] + plot_df['Small_Hydro_MV']
        plot_df['Total_Biomass'] = plot_df['Biomass_SCADA'] + plot_df['Biomass_MV']

        return plot_df, False 

    except Exception as e:
        print(f"Σφάλμα κατά την άντληση: {e}")
        return generate_dummy_data(), True

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

# 4. Εκτέλεση και Παραγωγή Γραφήματος
plot_df, is_dummy = fetch_and_parse()

title_status = "ΠΡΟΣΟΜΟΙΩΣΗ (Σφάλμα URL)" if is_dummy else "ΠΡΑΓΜΑΤΙΚΑ ΔΕΔΟΜΕΝΑ"

fig = px.bar(plot_df, 
             x='Hour', 
             y=['Total_Biomass', 'Total_Small_Hydro', 'Hydro_SCADA', 'Total_CHP', 'Total_PV', 'Wind_SCADA'],
             title=f'Ημερήσια Παραγωγή ΑΠΕ (MWh) - {date_str} [{title_status}]',
             labels={'value': 'Παραγωγή (MWh)', 'variable': 'Τεχνολογία'},
             barmode='stack',
             color_discrete_sequence=px.colors.qualitative.Pastel)

fig.write_html("index.html")
print("Η διαδικασία ολοκληρώθηκε.")
