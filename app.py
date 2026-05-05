from flask import Flask, render_template, request
import pandas as pd
import requests

app = Flask(__name__)

‏# הגדרות Mailjet
API_KEY = '89f6b99bc7bb58943ea4b5e998ab7e4d'
SECRET_KEY = '77445301940d666bcdb044b1f99a3e22'
SENDER_EMAIL = 'kobieliav@gmail.com'
# כאן הוספתי את שניכם כנמענים בצורה ברורה
RECIPIENTS = ['ishnab@gmail.com', 'kobieliav@gmail.com']

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            try:
                # קריאת הקובץ
                df = pd.read_csv(file, header=None) if file.filename.endswith('.csv') else pd.read_excel(file, header=None)
                
                summary_data = []
                current_p = None

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    
                    # זיהוי שם מטופל (עמודה 4)
                    potential_name = str(row[4]).strip() if pd.notna(row[4]) else ""
                    if potential_name and row.count() <= 2 and "תאריך" not in potential_name:
                        current_p = {
                            'full_name': potential_name,
                            'first_name': potential_name.split()[0],
                            'debt': "0",
                            'dates': []
                        }
                        summary_data.append(current_p)
                    
                    # זיהוי חוב (מתחת לכיתוב חוב כולל)
                    if any("חוב כולל" in s for s in row_list) and current_p:
                        current_p['debt'] = str(df.iloc[i + 1][5])
                    
                    # זיהוי תאריכי מפגשים (עמודה 0)
                    cell_0 = str(row[0])
                    if "/" in cell_0 and any(char.isdigit() for char in cell_0) and current_p:
                        is_cancelled = pd.notna(row[2]) and str(row[2]).strip() != ""
                        is_paid = pd.notna(row[8]) and str(row[8]).strip() != ""
                        if not is_cancelled and not is_paid:
                            current_p['dates'].append(cell_0)

                # בניית גוף המייל בעברית פשוטה
                email_body = "שלום אירית, להלן סיכום המפגשים:\n\n"
                for p in summary_data:
                    if p['dates']:
                        email_body += ‏f"עבור: {p['full_name']}\n"
                        email_body += ‏f"הי {p['first_name']},\n"
                        email_body += ‏f"בחודש האחרון היו לנו {len(p['dates'])} מפגשים בתאריכים: {', '.join(p['dates'])}\n"
                        email_body += ‏f"סה\"כ לתשלום: {p['debt']} ש\"ח.\n"
                        email_body += "תודה רבה!\n\n-------------------\n\n"

                ‏# שליחה דרך ה-API
                response = requests.post(
                    "https://api.mailjet.com/v3.1/send",
                    auth=(API_KEY, SECRET_KEY),
                    json={
                        'Messages': [{
                            "From": {"Email": SENDER_EMAIL, "Name": "Irit Billing"},
                            "To": [{"Email": email} for email in RECIPIENTS],
                            "Subject": "סיכום חובות חודשי - אירית",
                            "TextPart": email_body
                        }]
                    }
                )

                if response.status_code == 200 or response.status_code == 201:
                    return ‏'<h1>המייל נשלח בהצלחה!</h1><a href="/">חזרה</a>'
                else:
                    return ‏f"שגיאה בשליחה: {response.text}"

            except Exception as e:
                return ‏f"שגיאת מערכת: {str(e)}"
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
