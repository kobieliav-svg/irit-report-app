from flask import Flask, render_template, request
import pandas as pd
import requests
import os

app = Flask(__name__)

# Mailjet API Settings
MAILJET_API_KEY = '89f6b99bc7bb58943ea4b5e998ab7e4d'
MAILJET_SECRET_KEY = '77445301940d666bcdb044b1f99a3e22'
SENDER_EMAIL = 'kobieliav@gmail.com'
RECIPIENT_EMAILS = ['ishnab@gmail.com', 'kobieliav@gmail.com']

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            try:
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file, header=None)
                else:
                    df = pd.read_excel(file, header=None)

                patients_summary = []
                current_patient = None

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    potential_name = str(row[4]).strip() if pd.notna(row[4]) else ""
                    
                    if potential_name and row.count() <= 2 and "תאריך" not in potential_name:
                        current_patient = {
                            'full_name': potential_name, 
                            'first_name': potential_name.split()[0], 
                            'debt': "0", 
                            'dates': []
                        }
                        patients_summary.append(current_patient)
                    
                    if any("חוב כולל" in s for s in row_list) and current_patient:
                        current_patient['debt'] = str(df.iloc[i + 1][5])
                        
                    cell_0 = str(row[0])
                    if "/" in cell_0 and any(char.isdigit() for char in cell_0) and current_patient:
                        is_cancelled = pd.notna(row[2]) and str(row[2]).strip() != ""
                        is_paid = pd.notna(row[8]) and str(row[8]).strip() != ""
                        if not is_cancelled and not is_paid:
                            current_patient['dates'].append(cell_0)

                response = send_via_mailjet_api(patients_summary)
                if response.status_code == 200 or response.status_code == 201:
                    return '<h1>Success! The personalized report was sent.</h1><a href="/">Back</a>'
                else:
                    return f"Mailjet Error: {response.text}"
            except Exception as e:
                return f"System Error: {str(e)}"
    return render_template('upload.html')

def send_via_mailjet_api(patients_data):
    if not patients_data: return
    
    # הנוסח שאירית ביקשה
    message_body = "שלום אירית,\nלהלן ריכוז ההודעות לשליחה למטופלים:\n\n"
    message_body += "========================================\n\n"

    for p in patients_data:
        if not p['dates']: continue
        
        # הופך את רשימת התאריכים לטקסט מופרד בפסיקים
        dates_str = ", ".join(p['dates'])
        count = len(p['dates'])
        
        # בניית ההודעה האישית לכל מטופל
        message_body += ‏f"עבור: {p['full_name']}\n"
        message_body += ‏f"הי {p['first_name']},\n"
        message_body += ‏f"בחודש האחרון היו לנו {count} מפגשים בתאריכים: {dates_str}.\n"
        message_body += ‏f"סה\"כ לתשלום: {p['debt']} ש\"ח.\n"
        message_body += "תודה רבה והמשך יום נעים!\n"
        message_body += "\n----------------------------------------\n\n"
    
    data = {
        'Messages': [
            {
                "From": {"Email": SENDER_EMAIL, "Name": "Irit Billing System"},
                "To": [{"Email": email} for email in RECIPIENT_EMAILS],
                "Subject": "סיכום חודשי למטופלים - אירית",
                "TextPart": message_body
            }
        ]
    }
    
    res = requests.post(
        "https://api.mailjet.com/v3.1/send",
        auth=(MAILJET_API_KEY, MAILJET_SECRET_KEY),
        json=data
    )
    return res

if __name__ == "__main__":
    app.run(debug=True)
