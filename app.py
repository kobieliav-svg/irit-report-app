from flask import Flask, render_template, request
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)

‏# הגדרות Mailjet - המפתחות שלך כבר בפנים
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
                # בדיקת סיומת הקובץ וקריאה בהתאם
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file, header=None)
                else:
                    df = pd.read_excel(file, header=None)

                patients_summary = []
                current_patient = None

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    
                    # זיהוי שם מטופל (עמודה 4)
                    potential_name = str(row[4]).strip() if pd.notna(row[4]) else ""
                    if potential_name and row.count() <= 2 and "תאריך" not in potential_name:
                        current_patient = {
                            'full_name': potential_name, 
                            'first_name': potential_name.split()[0], 
                            'debt': "0", 
                            'dates': []
                        }
                        patients_summary.append(current_patient)
                    
                    # זיהוי חוב כולל (שורה מתחת לכותרת)
                    if any("חוב כולל" in s for s in row_list) and current_patient:
                        current_patient['debt'] = str(df.iloc[i + 1][5])
                        
                    # זיהוי תאריכים וסינון ביטולים/תשלומים
                    cell_0 = str(row[0])
                    if "/" in cell_0 and any(char.isdigit() for char in cell_0) and current_patient:
                        is_cancelled = pd.notna(row[2]) and str(row[2]).strip() != ""
                        is_paid = pd.notna(row[8]) and str(row[8]).strip() != ""
                        
                        if not is_cancelled and not is_paid:
                            current_patient['dates'].append(cell_0)

                send_via_mailjet(patients_summary)
                return '<h1>Success! The report was sent.</h1><a href="/">Back</a>'
            except Exception as e:
                return f"Error: {str(e)}"
    return render_template('upload.html')

def send_via_mailjet(patients_data):
    if not patients_data: return
    
    header = "שלום אירית, להלן סיכום הפגישות לחיוב:\n\n"
    body = ""
    for p in patients_data:
        if not p['dates']: continue
        
        dates_str = ", ".join(p['dates'])
        msg = ‏f"הי {p['first_name']},\n"
        msg += ‏f"בחודש האחרון היו לנו {len(p['dates'])} מפגשים בתאריכים: {dates_str}.\n"
        msg += ‏f"סה\"כ לתשלום: {p['debt']} ש\"ח.\n"
        msg += "תודה רבה והמשך יום נעים!\n"
        body += f"--- {p['full_name']} ---\n{msg}\n\n"
    
    msg = MIMEText(header + body, 'plain', 'utf-8')
    msg['Subject'] = 'Monthly Summary Report'
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(RECIPIENT_EMAILS)

    ‏# שליחה דרך השרת של Mailjet (פורט 587 פתוח עבורם ב-Render)
    with smtplib.SMTP('in-v3.mailjet.com', 587) as server:
        server.starttls()
        server.login(MAILJET_API_KEY, MAILJET_SECRET_KEY)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAILS, msg.as_string())

if __name__ == "__main__":
    app.run(debug=True)
