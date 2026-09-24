import pandas as pd

# Εδώ τρέχει η λογική σου: ανάγνωση SCADA, scraping, ή parsing API
df = pd.read_csv('historical_data.csv') 

# Εξαγωγή σε ένα ελαφρύ JSON αρχείο αντί για HTML
# Το orient='records' φτιάχνει μια λίστα από dictionaries (τέλειο για JS)
df.to_json('data.json', orient='records', force_ascii=False)

print("Το data.json ενημερώθηκε επιτυχώς!")
