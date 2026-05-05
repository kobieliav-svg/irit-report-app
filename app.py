from flask import Flask, render_template, request
import pandas as pd
import requests
from datetime import datetime

app = Flask(__name__)

# Config
MJ_AK = '89f6b99bc7bb58943ea4b5e998ab7e4d'
MJ_SK = '77445301940d666bcdb044b1f99a3e22'
SENDER = 'kobieliav@gmail.com'
RECIPIENTS = ['ishnab@gmail.com', 'kobieliav@gmail.com']

def get_target_month():
    months = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
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
                m_name = get_target_month()

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    full_name = str(row[4]).strip() if pd.notna(row[4]) else ""
                    
                    if full_name and row.count() <= 2 and "תאריך" not in full_name:
                        curr = {'full': full_name, 'first': full_name.split()[0], 'debt': "0", 'dates': []}
                        summary.append(curr)
                    
                    if any("חוב" in s and "כולל" in s for s in row_list) and curr:
                        debt_val = df.iloc[i + 1][5] if pd.notna(df.iloc[i + 1][5]) else df.iloc[i + 1][6]
                        curr['debt'] = str(debt_val) if pd.notna(debt_val) else "0"
                    
                    v0 = str(row[0])
                    if "/" in v0 and any(c.isdigit() for c in v0) and curr:
                        if not (pd.notna(row[2]) and str(row[2]).strip()) and not (pd.notna(row[8]) and str(row[8]).strip()):
                            curr['dates'].append(v0)

                body = ‏f"שלום אירית, להלן סיכום חובות עבור חודש {m_name}:\n\n"
                for p in summary:
                    if p['dates']:
                        body += ‏f"עבור: {p['full']}\n"
                        body += ‏f"הי {p['first']}, במהלך חודש {m_name} היו לנו {len(p['dates'])} מפגשים בתאריכים: {', '.join(p['dates'])}\n"
                        body += ‏f"סה\"כ לתשלום: {p['debt']} ש\"ח.\n"
                        body += "תודה רבה!\n\n-------------------\n\n"

                res = requests.post("https://api.mailjet.com/v3.1/send", auth=(MJ_AK, MJ_SK), json={
                    'Messages': [{
                        'From': {'Email': SENDER, 'Name': 'Irit System'}, 
                        'To': [{'Email': e} for e in RECIPIENTS], 
                        'Subject': ‏f'דיווח חובות חודשי - {m_name}', 
                        'TextPart': body
                    }]
                })
                
                return '<h1>Success! The report was sent.</h1>' if res.status_code < 300 else f'Error: {res.text}'
            except Exception as e:
                return f"System Error: {str(e)}"
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
