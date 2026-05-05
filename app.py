from flask import Flask, render_template, request
import pandas as pd
import requests
from datetime import datetime

app = Flask(__name__)

MJ_AK = '89f6b99bc7bb58943ea4b5e998ab7e4d'
MJ_SK = '77445301940d666bcdb044b1f99a3e22'
SENDER = 'kobieliav@gmail.com'
RECIPIENTS = ['ishnab@gmail.com', 'kobieliav@gmail.com']

def get_target_month():
    months = ["\u05d9\u05e0\u05d5\u05d0\u05e8", "\u05e4\u05d1\u05e8\u05d5\u05d0\u05e8", "\u05de\u05e8\u05e5", "\u05d0\u05e4\u05e8\u05d9\u05dc", "\u05de\u05d0\u05d9", "\u05d9\u05d5\u05e0\u05d9", "\u05d9\u05d5\u05dc\u05d9", "\u05d0\u05d5\u05d2\u05d5\u05e1\u05d8", "\u05e1\u05e4\u05d8\u05de\u05d1\u05e8", "\u05d0\u05d5\u05e7\u05d8\u05d5\u05d1\u05e8", "\u05e0\u05d5\u05d1\u05de\u05d1\u05e8", "\u05d3\u05e6\u05de\u05d1\u05e8"]
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
                
                t_date = "\u05ea\u05d0\u05e8\u05d9\u05da"
                t_debt = "\u05d7\u05d5\u05d1"
                t_total = "\u05db\u05d5\u05dc\u05dc"

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    full_name = str(row[4]).strip() if pd.notna(row[4]) else ""
                    
                    if full_name and row.count() <= 2 and t_date not in full_name:
                        curr = {'full': full_name, 'first': full_name.split()[0], 'debt': "0", 'dates': []}
                        summary.append(curr)
                    
                    if any(t_debt in s and t_total in s for s in row_list) and curr:
                        debt_val = df.iloc[i + 1][5] if pd.notna(df.iloc[i + 1][5]) else df.iloc[i + 1][6]
                        curr['debt'] = str(debt_val) if pd.notna(debt_val) else "0"
                    
                    v0 = str(row[0])
                    if "/" in v0 and any(c.isdigit() for c in v0) and curr:
                        if not (pd.notna(row[2]) and str(row[2]).strip()) and not (pd.notna(row[8]) and str(row[8]).strip()):
                            curr['dates'].append(v0)

                b_hi_irit = "\u05e9\u05dc\u05d5\u05dd \u05d0\u05d9\u05e8\u05d9\u05ea, \u05dc\u05d4\u05dc\u05df \u05e1\u05d9\u05db\u05d5\u05dd \u05d7\u05d5\u05d1\u05d5\u05ea \u05e2\u05d1\u05d5\u05e8 \u05d7\u05d5\u05d1\u05e9 "
                b_for = "\u05e2\u05d1\u05d5\u05e8: "
                b_hi = "\u05d4\u05d9 "
                b_during = ", \u05d1\u05de\u05d4\u05dc\u05da \u05d7\u05d5\u05d3\u05e9 "
                b_meetings = " \u05d4\u05d9\u05d5 \u05dc\u05e0\u05d5 "
                b_count = " \u05de\u05e4\u05d3\u05e9\u05d9\u05dd \u05d1\u05ea\u05d0\u05e8\u05d9\u05db\u05d9\u05dd: "
                b_total = "\u05e1\u05d4\"\u05db \u05dc\u05ea\u05e9\u05dc\u05d5\u05dd: "
                b_shekel = " \u05e9\"\u05d7. \u05ea\u05d5\u05d3\u05d4 \u05e8\u05d1\u05d4!"

                body = b_hi_irit + m_name + ":\n\n"
                for p in summary:
                    if p['dates']:
                        body += b_for + p['full'] + "\n"
                        body += b_hi + p['first'] + b_during + m_name + b_meetings + str(len(p['dates'])) + b_count + ", ".join(p['dates']) + "\n"
                        body += b_total + p['debt'] + b_shekel + "\n\n---\n\n"

                res = requests.post("https://api.mailjet.com/v3.1/send", auth=(MJ_AK, MJ_SK), json={
                    'Messages': [{'From': {'Email': SENDER, 'Name': 'Irit System'}, 
                                 'To': [{'Email': e} for e in RECIPIENTS], 
                                 'Subject': 'Billing Report', 
                                 'TextPart': body}]
                })
                
                return '<h1>Success!</h1>' if res.status_code < 300 else f'Error: {res.text}'
            except Exception as e:
                return f"Error: {str(e)}"
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
