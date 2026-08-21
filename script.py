import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Βρίσκουμε τη χθεσινή ημερομηνία (συνήθως ο ΑΔΜΗΕ βγάζει τα στοιχεία της προηγούμενης μέρας)
date_target = datetime.now() - timedelta(days=1)
date_str = date_target.strftime('%Y%m%d')

print(f"Προσπάθεια δημιουργίας γραφήματος για: {date_str}")

# --- ΕΔΩ ΘΑ ΜΠΕΙ Η ΛΟΓΙΚΗ ΤΟΥ ΚΑΤΕΒΑΣΜΑΤΟΣ ---
# Επειδή δεν ξέρουμε ακριβώς τα ονόματα των στηλών, φτιάχνουμε τον σκελετό
# Αν τα αρχεία δεν βρεθούν, θα φτιάξει ένα κενό γράφημα για να μην σκάσει το σύστημα.

try:
    # Προς το παρόν, δημιουργούμε "εικονικά" (dummy) δεδομένα για να στηθεί το dashboard.
    # Όταν πας σε υπολογιστή, θα αντικαταστήσουμε αυτό το μπλοκ με το πραγματικό διάβασμα των Excel.
    
    hours = list(range(1, 25))
    data = {
        'Hour': hours,
        'Wind_SCADA': [50] * 24, # Εικονικά 50 MWh
        'Total_PV': [0,0,0,0,0,0,10,30,50,80,100,120,120,100,80,50,30,10,0,0,0,0,0,0], # Καμπύλη Ήλιου
        'Total_CHP': [20] * 24,
        'Hydro_SCADA': [10] * 24,
        'Total_Small_Hydro': [5] * 24,
        'Total_Biomass': [2] * 24
    }
    
    plot_df = pd.DataFrame(data)

    # Δημιουργία του Stacked Bar Chart
    fig = px.bar(plot_df, 
                 x='Hour', 
                 y=['Wind_SCADA', 'Total_PV', 'Total_CHP', 'Hydro_SCADA', 'Total_Small_Hydro', 'Total_Biomass'],
                 title=f'Ημερήσια Παραγωγή ΑΠΕ (MWh) - Προσομοίωση για {date_str}',
                 labels={'value': 'Παραγωγή (MWh)', 'variable': 'Τεχνολογία'},
                 barmode='stack',
                 color_discrete_sequence=px.colors.qualitative.Pastel)

    # Σώσιμο σε HTML σελίδα
    fig.write_html("index.html")
    print("Το γράφημα δημιουργήθηκε με επιτυχία!")

except Exception as e:
    print(f"Σφάλμα: {e}")
