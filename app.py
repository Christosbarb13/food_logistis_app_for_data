import sys
import pandas as pd 
# Λέμε στην Python να εκτυπώνει πάντα σε UTF-8 για να βλέπουμε Ελληνικά
sys.stdout.reconfigure(encoding='utf-8')

#δημιουργώ το αρχείο excel με τα δεδομένα που θα χρησιμοποιήσω για την εφαρμογή και δινω την δυνατόητα να επιλέξει ο χρήστης ποιο φύλλο θέλει να χρησιμοποιήσει και να δει τα δεδομένα του επιλεγμένου φύλλου   
try:    
    excel_file="C:\\Users\\cris-\\OneDrive\\Desktop\\python\\efarmogi_mistotrofodosia\\ΙΟΥΝΙΟΣ (1).xlsx"
    xl=pd.ExcelFile(excel_file)
    print("Το αρχείο excel φορτώθηκε επιτυχώς")

    print("Τα φυλλά που περιέχει το αρχείο excel είναι τα εξής:")
    for i,sheet in enumerate(xl.sheet_names,1):
        print(f"{i}: {sheet}")
    choice=input("Επιλέξτε το φύλλο που θέλετε να χρησιμοποιήσετε (πληκτρολογήστε τον αριθμό του φύλλου): ")
    choice=int(choice)
    index=choice-1

    epilegmeno_fillo=xl.sheet_names[index]
    print(f"Το επιλεγμένο φύλλο είναι: {epilegmeno_fillo}")
    df=pd.read_excel(excel_file,sheet_name=epilegmeno_fillo)
    print("Τα δεδομένα του επιλεγμένου φύλλου είναι τα εξής:")
    print(df.head(10))

    kathato_df=df[df.columns[4]]
        
except FileNotFoundError:
    print("Το αρχείο excel δεν βρέθηκε. Παρακαλώ ελέγξτε το όνομα του αρχείου και τη διαδρομή του.")
except ValueError:
    print("Παρακαλώ εισάγετε έναν έγκυρο αριθμό φύλλου.")






