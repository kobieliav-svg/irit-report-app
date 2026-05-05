from flask import Flask, render_template, request
import pandas as pd
import requests
from datetime import datetime

app = Flask(__name__)

# Credentials
MJ_AK = '89f6b99bc7bb58943ea4b5e998ab7e4d'
MJ_SK = '77445301940d666bcdb044b1f99a3e22'
SENDER = 'kobieliav@gmail.com'
RECIPIENTS = ['ishnab@gmail.com', 'kobieliav@gmail.com']

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        if f:
            try:
                df = pd.read_csv(f, header=None) if f.filename.endswith('.csv') else pd.read_excel(f, header=None)
                summary = []
                curr = None
                
                # Use plain English keys internally to avoid issues
                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    name = str(row[4]).strip() if pd.notna(row[4]) else ""
                    
                    if name and row.count() <= 2 and "תאריך" not in name:
                        curr = {'full': name, 'first': name.split()[0], 'debt': "0", 'dates': []}
                        summary.append(curr)
                    
                    if any("חוב" in s and "כולל" in s for s in row_list) and curr:
                        val = df.iloc[i + 1][5] if pd.notna(df.iloc[i + 1][5]) else df.iloc[i + 1][6]
                        curr['debt'] = str(val) if pd.notna(val) else "0"
                    
                    v0 = str(row[0])
                    if "/" in v0 and any(c.isdigit() for c in v0) and curr:
                        if not (pd.notna(row[2]) and str(row[2]).strip()) and not (pd.notna(row[8]) and str(row[8]).strip()):
                            curr['dates'].append(v0)

                # Build the email
                body = "שלום אירית, להלן הדיווח:\n\n"
                for p in summary:
                    if p['dates']:
                        body += ‏f"עבור: {p['full']}\nהי {p['first']}, במהלך חודש אפריל היו לנו {len(p['dates'])} מפגשים בתאריכים: {', '.join(p['dates'])}\nסה\"כ לתשלום: {p['debt']} ש\"ח.\nתודה!\n\n---\n\n"

                # Send via Mailjet
                res = requests.post("https://api.mailjet.com/v3.1/send", 
                                    auth=(MJ_AK, MJ_SK), 
                                    timeout=15,
                                    json={
                    'Messages': [{
                        'From': {'Email': SENDER, 'Name': 'Irit System'}, 
                        'To': [{'Email': e} for e in RECIPIENTS], 
                        'Subject': 'Billing Report April', 
                        'TextPart': body
                    }]
                })
                
                # Detailed response for debugging
                if res.status_code < 300:
                    return f'<h1>Success! Mailjet ID: {res.json()["Messages"][0]["Status"]}</h1>'
                else:
                    return f'<h1>Mailjet Error: {res.status_code}</h1><p>{res.text}</p>'
                    
            except Exception as e:
                return f"<h1>Internal Error</h1><p>{str(e)}</p>"
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
