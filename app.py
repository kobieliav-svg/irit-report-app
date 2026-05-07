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

# All Hebrew keywords defined strictly as Unicode escape sequences
‏# K_DEBT = חוב כולל מטופל
K_DEBT = "\u05d7\u05d5\u05d1 \u05db\u05d5\u05dc\u05dc \u05de\u05d8\u05d5\u05e4\u05dc"
‏# K_DET = פירוט
K_DET = "\u05e4\u05d9\u05e8\u05d5\u05d8"
‏# M_HI = הי
M_HI = "\u05d4\u05d9"
‏# M_TOTAL = סהכ לתשלום
M_TOTAL = "\u05e1\u05d4\"\u05db \u05dc\u05ea\u05e9\u05dc\u05d5\u05dd"

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files.get('file')
        if f:
            try:
                # Reading the CSV with flexible engine
                df = pd.read_csv(f, header=None, encoding='utf-8-sig', sep=',', engine='python')
                
                summary = []
                curr = None

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist() if pd.notna(val)]
                    row_str = " ".join(row_list)

                    # Identify name in rows like "-------------- Name --------------"
                    if "--------------" in row_str:
                        match = re.search(r'-+\s*(.*?)\s*-+', row_str)
                        if match:
                            raw_name = match.group(1)
                            if K_DET not in raw_name:
                                name = raw_name.strip()
                                if name and (not curr or name != curr['f']):
                                    curr = {'f': name, 's': name.split()[0], 'd': "0", 'dt': []}
                                    summary.append(curr)

                    # Identify date in column 0
                    v0 = str(row[0]).strip()
                    if re.match(r'\d{1,2}/\d{1,2}/\d{4}', v0) and curr:
                        curr['dt'].append(v0)

                    # Identify debt amount
                    if K_DEBT in row_str and curr:
                        if i + 1 < len(df):
                            next_row = [str(x) for x in df.iloc[i+1].tolist()]
                            for val in next_row:
                                num = re.sub(r'[^\d.]', '', val)
                                if num and float(num) > 10:
                                    curr['d'] = str(int(float(num)))
                                    break

                # Building the email body using only ASCII and Unicode escapes
                body = "Billing Report:\n\n"
                valid_count = 0
                for p in summary:
                    if p['dt'] and p['d'] != "0":
                        valid_count += 1
                        body += p['f'] + ":\n"
                        body += M_HI + " " + p['s'] + ", " + str(len(p['dt'])) + " meetings: " + ", ".join(p['dt']) + "\n"
                        body += M_TOTAL + ": " + p['d'] + "\n\n---\n\n"

                if valid_count > 0:
                    requests.post("https://api.mailjet.com/v3.1/send", auth=(AK, SK), json={
                        'Messages': [{'From': {'Email': S, 'Name': 'Irit'}, 
                                     'To': [{'Email': e} for e in R], 
                                     'Subject': 'Billing Report', 'TextPart': body}]
                    })
                    return f"<h1>Success! Sent {valid_count} summaries.</h1>"
                return "<h1>No valid data found in file.</h1>"

            except Exception as e:
                return f"<h1>Error: {str(e)}</h1>"
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
