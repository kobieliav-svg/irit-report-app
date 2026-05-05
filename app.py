from flask import Flask, render_template, request
import pandas as pd
import requests

app = Flask(__name__)

# Config
AK = '89f6b99bc7bb58943ea4b5e998ab7e4d'
SK = '77445301940d666bcdb044b1f99a3e22'
S = 'kobieliav@gmail.com'
R = ['ishnab@gmail.com', 'kobieliav@gmail.com']

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        if f:
            try:
                df = pd.read_csv(f, header=None) if f.filename.endswith('.csv') else pd.read_excel(f, header=None)
                summary = []
                curr = None
                
                # Hebrew terms in hex
                t_date = b'\xd7\xaa\xd7\x90\xd7\xa8\xd7\x99\xd7\xaa'.decode('utf-8')
                t_debt = b'\xd7\x9d\xd7\x95\xd7\x91 \xd7\x9b\xd7\x95\xd7\x9c\xd7\x9c'.decode('utf-8')

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    name = str(row[4]).strip() if pd.notna(row[4]) else ""
                    if name and row.count() <= 2 and t_date not in name:
                        curr = {'f': name, 's': name.split()[0], 'd': "0", 'dt': []}
                        summary.append(curr)
                    if any(t_debt in s for s in row_list) and curr:
                        val = df.iloc[i + 1][5] if pd.notna(df.iloc[i + 1][5]) else df.iloc[i + 1][6]
                        curr['d'] = str(val) if pd.notna(val) else "0"
                    v0 = str(row[0])
                    if "/" in v0 and any(c.isdigit() for c in v0) and curr:
                        if not (pd.notna(row[2]) and str(row[2]).strip()) and not (pd.notna(row[8]) and str(row[8]).strip()):
                            curr['dt'].append(v0)

                # Hebrew body parts in hex
                h_hi_i = b'\xd7\xa9\xd7\x9c\xd7\x95\xd7\x9d \xd7\x90\xd7\x99\xd7\xa8\xd7\x99\xd7\xaa, \xd7\x9c\xd7\x94\xd7\x9c\xd7\x9f \xd7\x94\xd7\x93\xd7\x99\xd7\x95\xd7\x95\xd7\xad:'.decode('utf-8')
                h_for = b'\xd7\xa2\xd7\x91\xd7\x95\xd7\xa8: '.decode('utf-8')
                h_hi = b'\xd7\x94\xd7\x99 '.decode('utf-8')
                h_p1 = b', \xd7\x91\xd7\xad\xd7\x95\xd7\x93\xd7\xa9 \xd7\x90\xd7\x94\xd7\xa8\xd7\x99\xd7\x9c \xd7\x94\xd7\x99\xd7\x95 \xd7\x9c\xd7\xaa\xd7\x95 '.decode('utf-8')
                h_p2 = b' \xd7\x9e\xd7\xa4\xd7\x92\xd7\xa9\xd7\x99\xd7\x9d \xd7\x91\xd7\xaa\xd7\x90\xd7\xa8\xd7\x99\xd7\x9a\xd7\x99\xd7\x9d: '.decode('utf-8')
                h_p3 = b'. \xd7\xa1\xd7\x94"\xd7\x9b \xd7\x9c\xd7\xaa\xd7\xa9\xd7\x9c\xd7\x95\xd7\x9d: '.decode('utf-8')
                h_p4 = b' \xd7\xa9"\xd7\x97. \xd7\xaa\xd7\x95\xd7\x93\xd7\x94!'.decode('utf-8')

                body = h_hi_i + "\n\n"
                for p in summary:
                    if p['dt']:
                        body += f"{h_for}{p['f']}\n{h_hi}{p['s']}{h_p1}{len(p['dt'])}{h_p2}{', '.join(p['dt'])}\n{h_p3}{p['d']}{h_p4}\n\n---\n\n"

                res = requests.post("https://api.mailjet.com/v3.1/send", auth=(AK, SK), json={
                    'Messages': [{'From': {'Email': S}, 'To': [{'Email': e} for e in R], 'Subject': 'Report April', 'TextPart': body}]
                })
                
                return f'Success! Status: {res.status_code}'
            except Exception as e:
                return str(e)
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
