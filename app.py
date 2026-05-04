from flask import Flask, render_template, request
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)

# הגדרות אימייל - שימוש במשתני סביבה או בערכי ברירת מחדל
sender_email = os.environ.get('SENDER_EMAIL', 'kobieliav@gmail.com')
recipient_emails = ['ishnab@gmail.com', 'kobieliav@gmail.com']
email_password = os.environ.get('EMAIL_PASSWORD', 'qiga cxap rcwl qdag')

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            try:
                ‏# קריאת הקובץ (CSV או אקסל)
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
                        first_name = potential_name.split()[0] if potential_name else ""
                        current_patient = {
                            'full_name': potential_name,
                            'first_name': first_name,
                            'debt': "0",
                            'dates': []
                        }
                        patients_summary.append(current_patient)

                    # שליפת סכום החוב (שורה מתחת ל"חוב כולל")
                    if any("חוב כולל" in s for s in row_list):
                        data_row = df.iloc[i + 1]
                        if current_patient:
                            current_patient['debt'] = str(data_row[5])

                    # עיבוד תאריכי פגישות עם סינון ביטולים ותשלומים
                    cell_0 = str(row[0])
                    if "/" in cell_0 and any(char.isdigit() for char in cell_0):
                        if current_patient:
                            # בדיקה אם יש ביטול (עמודה 2) או תאריך תשלום (עמודה 8)
                            is_cancelled = pd.notna(row[2]) and str(row[2]).strip() != ""
                            is_paid = pd.notna(row[8]) and str(row[8]).strip() != ""
                            
                            if not is_cancelled and not is_paid:
                                current_patient['dates'].append(cell_0)

                send_email(patients_summary)
                return ‏'<h1>הקובץ עובד בהצלחה! המייל נשלח.</h1><a href="/">חזרה</a>'
            except Exception as e:
                return f"Error: {str(e)}"
    return render_template('upload.html')

def send_email(patients_data):
    if not patients_data: return
    
    header = "שלום אירית, להלן סיכום הפגישות לחיוב:\n\n"
    body = ""
    for p in patients_data:
        if not p['dates']: continue # דילוג על מטופל ללא פגישות לחיוב
        
        dates_str = ", ".join(p['dates'])
        msg = ‏f"הי {p['first_name']},\n"
        msg += ‏f"בחודש אפריל היו לנו {len(p['dates'])} מפגשים בתאריכים: {dates_str}.\n"
        msg += ‏f"סה\"כ לתשלום: {p['debt']} ש\"ח.\n"
        msg += "תודה רבה והמשך יום נעים!\n"
        body += f"--- {p['full_name']} ---\n{msg}\n\n"
    
    msg = MIMEText(header + body, 'plain', 'utf-8')
    msg['Subject'] = 'סיכום פגישות חודשי'
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipient_emails)
    
    ‏# שימוש בפורט 465 (SSL) שנחשב יציב יותר בשרתי ענן למניעת Timeout
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, email_password)
        server.sendmail(sender_email, recipient_emails, msg.as_string())

if __name__ == "__main__":
    app.run(debug=True)
