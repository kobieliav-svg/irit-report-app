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
                
                # Hebrew search terms
                t_date = "תאריך"
                t_debt = "חוב כולל"

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

                # Email Body Construction
                body = "שלום אירית, להלן סיכום המפגשים עבור חודש אפריל:\n\n"
                for p in summary:
                    if p['dt']:
                        body += f"עבור: {p['f']}\n"
                        body += ‏f"הי {p['s']}, במהלך חודש אפריל היו לנו {len(p['dt'])} מפגשים בתאריכים: {', '.join(p['dt'])}\n"
                        body += f"סה\"כ לתשלום: {p['d']} ש\"ח.\n"
                        body += "תודה רבה!\n\n-------------------\n\n"

                res = requests.post("https://api.mailjet.com/v3.1/send", auth=(AK, SK), json={
                    'Messages': [{
                        'From': {'Email': S, 'Name': 'Irit Billing'}, 
                        'To': [{'Email': e} for e in R], 
                        'Subject': 'סיכום חובות חודשי - אפריל', 
                        'TextPart': body
                    }]
                })
                
                return '<h1>Success! The report was sent.</h1>'
            except Exception as e:
                return str(e)
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
