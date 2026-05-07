from flask import Flask, render_template, request
import pandas as pd
import requests
import re
import sys

app = Flask(__name__)

# --- Configuration ---
AK = '89f6b99bc7bb58943ea4b5e998ab7e4d'
SK = '77445301940d666bcdb044b1f99a3e22'
S = 'kobieliav@gmail.com'
R = ['ishnab@gmail.com', 'kobieliav@gmail.com']

# --- Unicode Strings ---
T_DATE = "\u05ea\u05d0\u05e8\u05d9\u05da"
T_DEBT = "\u05d7\u05d5\u05d1 \u05db\u05d5\u05dc\u05dc"
M_TITLE = "\u05e9\u05dc\u05d5\u05dd \u05d0\u05d9\u05e8\u05d9\u05ea, \u05dc\u05d4\u05dc\u05df \u05e1\u05d9\u05db\u05d5\u05dd \u05d4\u05de\u05e4\u05d2\u05e9\u05d9\u05dd:"
M_FOR = "\u05e2\u05d1\u05d5\u05e8: "
M_HI = "\u05d4\u05d9 "
M_P1 = ", \u05d1\u05de\u05d4\u05dc\u05da \u05d4\u05d7\u05d5\u05d3\u05e9 \u05d4\u05d9\u05d5 \u05dc\u05e0\u05d5 "
M_P2 = " \u05de\u05e4\u05d2\u05e9\u05d9\u05dd \u05d1\u05ea\u05d0\u05e8\u05d9\u05db\u05d9\u05dd: "
M_P3 = "\u05e1\u05d4\"\u05db \u05dc\u05ea\u05e9\u05dc\u05d5\u05dd: "
M_P4 = " \u05e9\"\u05d7. \u05ea\u05d5\u05d3\u05d4 \u05e8\u05d1\u05d4!"

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files.get('file')
        if f:
            try:
                if f.filename.endswith('.csv'):
                    df = pd.read_csv(f, header=None, encoding='utf-8-sig')
                else:
                    df = pd.read_excel(f, header=None)
                
                summary = []
                curr = None

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    
                    # 1. Patient Identification
                    raw_name = str(row[4]).strip() if len(row) > 4 and pd.notna(row[4]) else ""
                    clean_name = re.sub(r'[-/._*]{2,}', '', raw_name).strip()
                    
                    if clean_name and T_DATE not in clean_name and "/" not in str(row[0]):
                        if len(clean_name) > 2:
                            curr = {'f': clean_name, 's': clean_name.split()[0], 'd': "0", 'dt': []}
                            summary.append(curr)

                    # 2. Debt Extraction
                    if any(T_DEBT in s for s in row_list) and curr:
                        val = df.iloc[i + 1][5] if pd.notna(df.iloc[i + 1][5]) else df.iloc[i + 1][6]
                        if pd.notna(val):
                            curr['d'] = re.sub(r'[^\d.]', '', str(val))

                    # 3. Dates Extraction
                    v0 = str(row[0])
                    if "/" in v0 and any(c.isdigit() for c in v0) and curr:
                        if len(row) > 2 and (not str(row[2]).strip() or str(row[2]) == "nan"):
                            curr['dt'].append(v0)

                # --- Build Email ---
                body = M_TITLE + "\n\n"
                valid_count = 0
                for p in summary:
                    if p['dt'] and p['d'] != "0":
                        valid_count += 1
                        body += M_FOR + p['f'] + "\n"
                        body += M_HI + p['s'] + M_P1 + str(len(p['dt'])) + M_P2 + ", ".join(p['dt']) + "\n"
                        body += M_P3 + p['d'] + M_P4 + "\n\n---\n\n"

                if valid_count == 0:
                    body = "No data identified in file."

                requests.post("https://api.mailjet.com/v3.1/send", auth=(AK, SK), json={
                    'Messages': [{'From': {'Email': S, 'Name': 'Irit Billing'}, 
                                 'To': [{'Email': e} for e in R], 
                                 'Subject': 'Billing Summary', 
                                 'TextPart': body}]
                })
                
                return f"<h1>Success! Sent summaries for {valid_count} patients.</h1>"
            except Exception as e:
                return f"<h1>Error: {str(e)}</h1>"
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
