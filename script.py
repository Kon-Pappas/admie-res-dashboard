import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

# 1. Ημερομηνία αναφοράς (Χθεσινή μέρα)
date_target = datetime.now() - timedelta(days=1)
date_str = date_target.strftime('%Y-%m-%d')

print(f"Επεξεργασία δεδομένων για την ημερομηνία: {date_str}")

csv_filename = "historical_data.csv"

# 2. Συνάρτηση δημιουργίας δεδομένων (Πραγματικών ή Προσομοίωσης)
def get_daily_data():
    # Εδώ στο μέλλον μπορούμε να προσθέσουμε την αυτοματοποιημένη ανάγνωση των excel σου.
    # Προς το παρόν, δημιουργούμε τα 24ωρα δεδομένα για να χτιστεί η βάση.
    hours = list(range(1, 25))
    df = pd.DataFrame({
        'Date': [date_str] * 24,
        'Hour': hours,
        'Wind_SCADA': [60 + (i%5)*2 for i in hours],
        'Total_PV': [0,0,0,0,0,0,15,40,70,100,130,150,150,130,100,70,40,15,0,0,0,0,0,0],
        'Total_CHP': [25] * 24,
        'Hydro_SCADA': [12] * 24,
        'Total_Small_Hydro': [6] * 24,
        'Total_Biomass': [3] * 24
    })
    return df

# Παίρνουμε τα δεδομένα της ημέρας
today_df = get_daily_data()

# 3. Διαχείριση του Ιστορικού CSV (Appending)
if os.path.exists(csv_filename):
    # Αν υπάρχει ήδη το αρχείο, διαβάζουμε το παλιό ιστορικό
    history_df = pd.read_csv(csv_filename)
    # Αφαιρούμε τυχόν διπλότυπη εγγραφή για την ίδια ημερομηνία (για να μην μπαίνει διπλή)
    history_df = history_df[history_df['Date'] != date_str]
    # Ενώνουμε το παλιό ιστορικό με τη σημερινή μέρα
    full_df = pd.concat([history_df, today_df], ignore_index=True)
else:
    # Αν δεν υπάρχει, το σημερινό γίνεται η αρχή του ιστορικού
    full_df = today_df

# Αποθηκεύουμε το ενημερωμένο CSV πίσω στο GitHub
full_df.to_csv(csv_filename, index=False)
print(f"Το αρχείο {csv_filename} ενημερώθηκε επιτυχώς!")

# 4. Δημιουργία Γραφήματος ΜΟΝΟ για τη χθεσινή/τελευταία μέρα
plot_df = full_df[full_df['Date'] == date_str]

if plot_df.empty:
    plot_df = today_df # Fallback αν κάτι πάει στραβά

fig = px.bar(plot_df, 
             x='Hour', 
             y=['Total_Biomass', 'Total_Small_Hydro', 'Hydro_SCADA', 'Total_CHP', 'Total_PV', 'Wind_SCADA'],
             title=f'Ημερήσια Παραγωγή ΑΠΕ (MWh) - Ημερομηνία: {date_str}',
             labels={'value': 'Παραγωγή (MWh)', 'variable': 'Τεχνολογία', 'Hour': 'Ώρα'},
             barmode='stack',
             color_discrete_sequence=px.colors.qualitative.Set2)

fig.update_xaxes(tickmode='linear', tick0=1, dtick=1)
fig.write_html("index.html")
print("Το dashboard (index.html) ανανεώθηκε!")
