from flask import Flask, render_template, request
import pandas as pd
import requests
from datetime import datetime

app = Flask(__name__)

# Credentials
MJ_AK = '89f6b99bc7bb58943ea4b5e998ab7e4d'
MJ_SK = '77445301940d666bcdb044b1f99a3e22'
FROM_E = 'kobieliav@gmail.com'
TO_E = ['ishnab@gmail.com', 'kobieliav@gmail.com']

def get_last_month_hebrew():
    months = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
    # מחסירים 1 מהחודש הנוכחי (מערך מתחיל ב-0, לכן -2 נותן את החודש הקודם)
    last_month_idx = (datetime.now().month - 2) % 12
    return months[last_month_idx]

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        if f:
            try:
                df = pd.read_csv(f, header=None) if f.filename.endswith('.csv') else pd.read_excel(f, header=None)
                summary = []
                curr = None
                month_name = get_last_month_hebrew()

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    
                    # זיהוי שם מטופל
                    name = str(row[4]).strip() if pd.notna(row[4]) else ""
                    if name and row.count() <= 2 and "תאריך" not in name:
                        curr = {
                            'full': name, 
                            'first': name.split()[0], 
                            'debt': "0", 
                            'dates': []
                        }
                        summary.append(curr)
                    
                    # זיהוי חוב כולל
                    if any("חוב" in s and "כולל" in s for s in row_list) and curr:
                        try:
                            # מחפש את הערך המספרי בשורה מתחת, בעמודות 5 או 6
                            debt_val = df.iloc[i + 1][5]
                            if pd.isna(debt_val) or str(debt_val).strip() == "":
                                debt_val = df.iloc[i + 1][6]
                            curr['debt'] = str(debt_val) if pd.notna(debt_val) else "0"
                        except:
                            curr['debt'] = "0"
                    
                    # זיהוי תאריכים (עמודה 0)
                    v0 = str(row[0])
                    if "/" in v0 and any(c.isdigit() for c in v0) and curr:
                        # וודא שאין ביטול (עמודה 2) ואין תשלום (עמודה 8)
                        is_cancelled = pd.notna(row[2]) and str(row[2]).strip() != ""
                        is_paid = pd.notna(row[8]) and str(row[8]).strip() != ""
                        if not is_cancelled and not is_paid:
                            curr['dates'].append(v0)

                # בניית המייל עם שם פרטי בלבד בפנייה
                body = ‏f"שלום אירית, להלן דיווח סיכום המפגשים עבור חודש {month_name}:\n\n"
                for p in summary:
                    if p['dates']:
                        body += ‏f"עבור: {p['full']}\n"
                        body += ‏f"הי {p['first']}, במהלך חודש {month_name} היו לנו {len(p['dates'])} מפגשים בתאריכים: {', '.join(p['dates'])}\n"
                        body += ‏f"סה\"כ לתשלום: {p['debt']} ש\"ח.\n"
                        body += "תודה רבה!\n\n-------------------\n\n"

                # שליחה
                res = requests.post("https://api.mailjet.com/v3.1/send", auth=(MJ_AK, MJ_SK), json={
                    'Messages': [{
                        'From': {'Email': FROM_E, 'Name': 'Irit Billing System'}, 
                        'To': [{'Email': e} for e in TO_E], 
                        'Subject': ‏f'דיווח חובות חודשי - {month_name}', 
                        'TextPart': body
                    }]
                })
                
                return ‏'<h1>המייל נשלח בהצלחה!</h1><a href="/">חזרה</a>' if res.status_code < 300 else f'Error: {res.text}'
            except Exception as e:
                return f"System Error: {str(e)}"
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
