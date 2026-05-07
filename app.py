from flask import Flask, render_template, request
import pandas as pd
import requests
import re

app = Flask(__name__)

# Credentials
AK = '89f6b99bc7bb58943ea4b5e998ab7e4d'
SK = '77445301940d666bcdb044b1f99a3e22'
S = 'kobieliav@gmail.com'
R = ['ishnab@gmail.com', 'kobieliav@gmail.com']

# Unicode Keywords (No Hebrew characters in code to avoid BiDi errors)
‏# T_DATE = תאריך | T_DEBT = חוב | M_TITLE = שלום אירית...
T_DATE = "\u05ea\u05d0\u05e8\u05d9\u05da"
T_DEBT = "\u05d7\u05d5\u05d1"
M_TITLE = "\u05e9\u05dc\u05d5\u05dd \u05d0\u05d9\u05e8\u05d9\u05ea, \u05dc\u05d4\u05dc\u05df \u05e1\u05d9\u05db\u05d5\u05dd \u05d4\u05de\u05e4\u05d2\u05e9\u05d9\u05dd:"

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files.get('file')
        if f:
            try:
                # Safe Load
                if f.filename.endswith('.csv'):
                    df = pd.read_csv(f, header=None, encoding='utf-8-sig')
                else:
                    df = pd.read_excel(f, header=None)
                
                summary = []
                curr = None

                for i, row in df.iterrows():
                    row_cells = [str(c).strip() for c in row.tolist()]
                    row_text = " ".join(row_cells)
                    
                    # 1. Identify Patient (Column E = Index 4)
                    val_e = str(row[4]).strip() if len(row) > 4 else ""
                    clean_name = re.sub(r'[-/._*]{2,}', '', val_e).strip()
                    
                    if clean_name and len(clean_name) > 1 and T_DATE not in clean_name:
                        if "/" not in str(row[0]):
                            curr = {'f': clean_name, 's': clean_name.split()[0], 'd': "0", 'dt': []}
                            summary.append(curr)

                    # 2. Extract Dates (Column A = Index 0)
                    v0 = str(row[0]).strip()
                    if "/" in v0 and any(c.isdigit() for c in v0) and curr:
                        curr['dt'].append(v0)

                    # 3. Extract Amount (Search near debt keyword)
                    if T_DEBT in row_text and curr:
                        search_rows = df.iloc[i:i+3]
                        for _, r in search_rows.iterrows():
                            for cell in r:
                                num_only = re.sub(r'[^\d]', '', str(cell))
                                if num_only and 100 <= int(num_only) <= 9999:
                                    curr['d'] = num_only
                                    break
                            if curr['d'] != "0": break

                # Build Body
                body = M_TITLE + "\n\n"
                valid_count = 0
                for p in summary:
                    if p['dt'] and p['d'] != "0":
                        valid_count += 1
                        body += f"{p['f']}: {len(p['dt'])} dates, {p['d']} total.\n"

                if valid_count > 0:
                    requests.post("https://api.mailjet.com/v3.1/send", auth=(AK, SK), json={
                        'Messages': [{'From': {'Email': S, 'Name': 'Irit'}, 
                                     'To': [{'Email': e} for e in R], 
                                     'Subject': 'Billing Update', 'TextPart': body}]
                    })
                    return f"<h1>Success! Sent {valid_count} messages.</h1>"
                return "<h1>No valid summaries found. Check file columns.</h1>"

            except Exception as e:
                return f"<h1>Error: {str(e)}</h1>"
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
