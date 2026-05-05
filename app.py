from flask import Flask, render_template, request
import pandas as pd
import requests

app = Flask(__name__)

# Credentials
MJ_AK = '89f6b99bc7bb58943ea4b5e998ab7e4d'
MJ_SK = '77445301940d666bcdb044b1f99a3e22'
FROM_E = 'kobieliav@gmail.com'
TO_E = ['ishnab@gmail.com', 'kobieliav@gmail.com']

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        if f:
            try:
                df = pd.read_csv(f, header=None) if f.filename.endswith('.csv') else pd.read_excel(f, header=None)
                summary = []
                curr = None
                
                # Search terms (Encoded to avoid invisible characters)
                t_date = b'\xd7\xaa\xd7\x90\xd7\xa8\xd7\x99\xd7\x9a'.decode('utf-8')
                t_debt = b'\xd7\x9d\xd7\x95\xd7\x91 \xd7\x9b\xd7\x95\xd7\x9c\xd7\x9c'.decode('utf-8')

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    name = str(row[4]).strip() if pd.notna(row[4]) else ""
                    if name and row.count() <= 2 and t_date not in name:
                        curr = {'full': name, 'first': name.split()[0], 'debt': "0", 'dates': []}
                        summary.append(curr)
                    if any(t_debt in s for s in row_list) and curr:
                        curr['debt'] = str(df.iloc[i + 1][5])
                    v0 = str(row[0])
                    if "/" in v0 and any(c.isdigit() for c in v0) and curr:
                        if not (pd.notna(row[2]) and str(row[2]).strip()) and not (pd.notna(row[8]) and str(row[8]).strip()):
                            curr['dates'].append(v0)

                # Build Hebrew Body using Safe Strings
                h1 = b'\xd7\xa9\xd7\x9c\xd7\x95\xd7\x9d \xd7\x90\xd7\x99\xd7\xa8\xd7\x99\xd7\xaa, \xd7\x9c\xd7\x94\xd7\x9c\xd7\x9f \xd7\x94\xd7\x93\xd7\x99\xd7\x95\xd7\x95\xd7\xad:'.decode('utf-8')
                h2 = b'\xd7\xa2\xd7\x91\xd7\x95\xd7\xa8: '.decode('utf-8')
                h3 = b'\xd7\x94\xd7\x99 '.decode('utf-8')
                h4 = b', \xd7\x91\xd7\xad\xd7\x95\xd7\x93\xd7\xa9 \xd7\x94\xd7\x90\xd7\xac\xd7\xa8\xd7\x95\xd7\x9f \xd7\x94\xd7\x99\xd7\x95 \xd7\x9c\xd7\xaa\xd7\x95 '.decode('utf-8')
                h5 = b' \xd7\x9e\xd7\xa4\xd7\x92\xd7\xa9\xd7\x99\xd7\x9d \xd7\x91\xd7\xaa\xd7\x90\xd7\xa8\xd7\x99\xd7\x9a\xd7\x99\xd7\x9d: '.decode('utf-8')
                h6 = b'. \xd7\xa1\xd7\x94"\xd7\x9b \xd7\x9c\xd7\xaa\xd7\xa9\xd7\x9c\xd7\x95\xd7\x9d: '.decode('utf-8')
                h7 = b' \xd7\xa9"\xd7\x97. \xd7\xaa\xd7\x95\xd7\x93\xd7\x94!'.decode('utf-8')

                body = h1 + "\n\n"
                for p in summary:
                    if p['dates']:
                        body += f"{h2}{p['full']}\n{h3}{p['first']}{h4}{len(p['dates'])}{h5}{', '.join(p['dates'])}\n{h6}{p['debt']}{h7}\n\n---\n\n"

                res = requests.post("https://api.mailjet.com/v3.1/send", auth=(MJ_AK, MJ_SK), json={
                    'Messages': [{'From': {'Email': FROM_E, 'Name': 'Irit'}, 'To': [{'Email': e} for e in TO_E], 'Subject': 'Irit Report', 'TextPart': body}]
                })
                
                return '<h1>Sent Successfully!</h1>' if res.status_code < 300 else f'Error: {res.text}'
            except Exception as e:
                return f"System Error: {str(e)}"
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
