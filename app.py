from flask import Flask, render_template, request
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)

# Settings from Environment Variables (Recommended) or fallback
sender_email = os.environ.get('SENDER_EMAIL', 'kobieliav@gmail.com')
recipient_emails = ['ishnab@gmail.com', 'kobieliav@gmail.com']
email_password = os.environ.get('EMAIL_PASSWORD', 'qiga cxap rcwl qdag')

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
                    
                    # Name identification (Column index 4)
                    potential_name = str(row[4]).strip() if pd.notna(row[4]) else ""
                    if potential_name and row.count() <= 2 and "\u05ea\u05d0\u05e8\u05d9\u05da" not in potential_name:
                        first_name = potential_name.split()[0] if potential_name else ""
                        current_patient = {
                            'full_name': potential_name,
                            'first_name': first_name,
                            'debt': "0",
                            'sessions_count': "0",
                            'dates': []
                        }
                        patients_summary.append(current_patient)

                    # Debt summary logic
                    if any("\u05d7\u05d5\u05d1\u0020\u05db\u05d5\u05dc\u05dc" in s for s in row_list):
                        data_row = df.iloc[i + 1]
                        if current_patient:
                            current_patient['debt'] = str(data_row[5])
                            current_patient['sessions_count'] = str(data_row[1])

                    # Date processing with validation for cancellations and payments
                    cell_0 = str(row[0])
                    if "/" in cell_0 and any(char.isdigit() for char in cell_0):
                        if current_patient:
                            # Validation: Check cancellation (Col 2) and Payment (Col 8)
                            is_cancelled = pd.notna(row[2]) and str(row[2]).strip() != ""
                            is_paid = pd.notna(row[8]) and str(row[8]).strip() != ""
                            
                            if not is_cancelled and not is_paid:
                                current_patient['dates'].append(cell_0)

                send_email(patients_summary)
                return 'Success'
            except Exception as e:
                return f"Error: {str(e)}"
    return render_template('upload.html')

def send_email(patients_data):
    if not patients_data: return
    header = "\u05e9\u05dc\u05d5\u05dd\u0020\u05d0\u05d9\u05e8\u05d9\u05ea\u002c\u0020\u05dc\u05d4\u05dc\u05df\u0020\u05e1\u05d9\u05db\u05d5\u05dd\u003a\n\n"
    body = ""
    for p in patients_data:
        dates_str = ", ".join(p['dates'])
        line = f"Patient: {p['full_name']}\n"
        # Template for: Hi {name}, in April...
        msg_template = "\u05d4\u05d9\u0020{name}\u002c\n\u05d1\u05d7\u05d5\u05d3\u05e9\u0020\u05d0\u05e4\u05e8\u05d9\u05dc\u0020\u05d4\u05d9\u05d5\u0020\u05dc\u05e0\u05d5\u0020{count}\u0020\u05de\u05e4\u05d2\u05e9\u05d9\u05dd\u0020\u05d1\u05ea\u05d0\u05e8\u05d9\u05db\u05d9\u05dd\u003a\u0020{dates}\u002e\n\u05e1\u05d4\u0022\u05db\u0020\u05dc\u05ea\u05e9\u05dc\u05d5\u05dd\u003a\u0020{debt}\u0020\u05e9\u0022\u05d7\u002e\n\u05ea\u05d5\u05d3\u05d4\u0020\u05e8\u05d1\u05d4\u0020\u05d5\u05d4\u05de\u05e9\u05da\u0020\u05d9\u05d5\u05dd\u0020\u05e0\u05e2\u05d9\u05dd\u0021\n"
        body += line + msg_template.format(name=p['first_name'], count=len(p['dates']), dates=dates_str, debt=p['debt']) + "--------------------------\n"
    
    msg = MIMEText(header + body, 'plain', 'utf-8')
    msg['Subject'] = 'Monthly Summary Report'
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipient_emails)
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, email_password)
        server.sendmail(sender_email, recipient_emails, msg.as_string())

if __name__ == "__main__":
    app.run(debug=True)