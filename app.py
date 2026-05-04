from flask import Flask, render_template, request
import pandas as pd
import requests

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
                
                # Encoded Hebrew terms to avoid SyntaxError
                term_date = b'\xd7\xaa\xd7\x90\xd7\xa8\xd7\x99\xd7\x9a'.decode('utf-8')
                term_debt = b'\xd7\x9d\xd7\x95\xd7\x91 \xd7\x9b\xd7\x95\xd7\x9c\xd7\x9c'.decode('utf-8')

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    potential_name = str(row[4]).strip() if pd.notna(row[4]) else ""
                    
                    if potential_name and row.count() <= 2 and term_date not in potential_name:
                        current_patient = {
                            'full_name': potential_name, 
                            'first_name': potential_name.split()[0], 
                            'debt': "0", 
                            'dates': []
                        }
                        patients_summary.append(current_patient)
                    
                    if any(term_debt in s for s in row_list) and current_patient:
                        current_patient['debt'] = str(df.iloc[i + 1][5])
                        
                    cell_0 = str(row[0])
                    if "/" in cell_0 and any(char.isdigit() for char in cell_0) and current_patient:
                        is_cancelled = pd.notna(row[2]) and str(row[2]).strip() != ""
                        is_paid = pd.notna(row[8]) and str(row[8]).strip() != ""
                        if not is_cancelled and not is_paid:
                            current_patient['dates'].append(cell_0)

                send_via_mailjet_api(patients_summary)
                return '<h1>Success! The report was sent.</h1><a href="/">Back</a>'
            except Exception as e:
                return f"System Error: {str(e)}"
    return render_template('upload.html')

def send_via_mailjet_api(patients_data):
    if not patients_data: return
    
    # Building the message using encoded Hebrew bits
    h_intro = b'\xd7\xa9\xd7\x9c\xd7\x95\xd7\x9d \xd7\x90\xd7\x99\xd7\xa8\xd7\x99\xd7\xaa, \xd7\x9c\xd7\x94\xd7\x9c\xd7\x9f \xd7\x94\xd7\x94\xd7\x95\xd7\x93\xd7\xa2\xd7\x95\xd7\xaa:'.decode('utf-8')
    h_for = b'\xd7\xa2\xd7\x91\xd7\x95\xd7\xa8: '.decode('utf-8')
    h_hi = b'\xd7\x94\xd7\x99 '.decode('utf-8')
    h_p1 = b', \xd7\x91\xd7\x9d\xd7\x95\xd7\x93\xd7\xa9 \xd7\x94\xd7\x90\xd7\xac\xd7\xa8\xd7\x95\xd7\x9f \xd7\x94\xd7\x99\xd7\x95 \xd7\x9c\xd7\xaa\xd7\x95 '.decode('utf-8')
    h_p2 = b' \xd7\x9e\xd7\xa4\xd7\x92\xd7\xa9\xd7\x99\xd7\x9d \xd7\x91\xd7\xaa\xd7\x90\xd7\xa8\xd7\x99\xd7\x9a\xd7\x99\xd7\x9d: '.decode('utf-8')
    h_p3 = b'. \xd7\xa1\xd7\x94"\xd7\x9b \xd7\x9c\xd7\xaa\xd7\xa9\xd7\x9c\xd7\x95\xd7\x9d: '.decode('utf-8')
    h_p4 = b' \xd7\xa9"\xd7\x97. \xd7\xaa\xd7\x95\xd7\x93\xd7\x94!'.decode('utf-8')

    body = h_intro + "\n\n"
    for p in patients_data:
        if not p['dates']: continue
        dates_str = ", ".join(p['dates'])
        body += f"{h_for}{p['full_name']}\n"
        body += f"{h_hi}{p['first_name']}{h_p1}{len(p['dates'])}{h_p2}{dates_str}\n"
        body += f"{h_p3}{p['debt']}{h_p4}\n"
        body += "\n-------------------\n\n"
    
    data = {
        'Messages': [
            {
                "From": {"Email": SENDER_EMAIL, "Name": "Irit Billing"},
                "To": [{"Email": email} for email in RECIPIENT_EMAILS],
                "Subject": "Monthly Billing Summary",
                "TextPart": body
            }
        ]
    }
    
    return requests.post(
        "https://api.mailjet.com/v3.1/send",
        auth=(MAILJET_API_KEY, MAILJET_SECRET_KEY),
        json=data
    )

if __name__ == "__main__":
    app.run(debug=True)
