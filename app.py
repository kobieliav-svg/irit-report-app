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

# --- Hebrew Keywords (Defined here to avoid encoding issues in logic) ---
KW_DATE = "\u05ea\u05d0\u05e8\u05d9\u05da" # תאריך
KW_DEBT = "\u05d7\u05d5\u05d1" # חוב
KW_PAY = "\u05dc\u05ea\u05e9\u05dc\u05d5\u05dd" # לתשלום
KW_DET = "\u05e4\u05d9\u05e8\u05d5\u05d8" # פירוט

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        if f:
            try:
                # Load file with safe encoding
                if f.filename.endswith('.csv'):
                    df = pd.read_csv(f, header=None, encoding='utf-8-sig')
                else:
                    df = pd.read_excel(f, header=None)
                
                summary = []
                curr = None
                
                print(f"DEBUG: Rows found: {len(df)}", file=sys.stderr)

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    row_str = " | ".join(row_list)
                    
                    # 1. Patient Name Logic (Column 4)
                    raw_name = str(row[4]).strip() if len(row) > 4 and pd.notna(row[4]) else ""
                    clean_name = re.sub(r'[-/._*]{2,}', '', raw_name).strip()
                    
                    if clean_name and len(clean_name) > 1 and "/" not in str(row[0]):
                        if KW_DATE not in clean_name and KW_DET not in clean_name:
                            curr = {'f': clean_name, 's': clean_name.split()[0], 'd': "0", 'dt': []}
                            summary.append(curr)

                    # 2. Dates Logic (Column 0)
                    v0 = str(row[0])
                    if "/" in v0 and any(c.isdigit() for c in v0) and curr:
                        if len(row) > 2 and (not str(row[2]).strip() or str(row[2]) == "nan"):
                            curr['dt'].append(v0)

                    # 3. Debt/Amount Logic
                    if (KW_DEBT in row_str or KW_PAY in row_str) and curr:
                        search_area = row_str
                        if i + 1 < len(df):
                            search_area += " | " + " ".join([str(x) for x in df.iloc[i+1].values])
                        
                        numbers = re.findall(r'\b\d{2,4}\b', search_area)
                        if numbers:
                            curr['d'] = numbers[-1]

                # --- Screen Output (Diagnostics) ---
                if not summary:
                    return "<h1>No Patients Found. Check Column E.</h1>"
                
                res_html = "<h2>Diagnostic Results:</h2><table border='1' dir='rtl'>"
                res_html += "<tr><th>Name</th><th>Count</th><th>Dates</th><th>Amount</th></tr>"
                for p in summary:
                    res_html += f"<tr><td>{p['f']}</td><td>{len(p['dt'])}</td><td>{', '.join(p['dt'])}</td><td>{p['d']}</td></tr>"
                res_html += "</table><br><a href='/'>Back</a>"
                
                return res_html

            except Exception as e:
                return f"<h1>Error: {str(e)}</h1>"
    
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
