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

# Keywords as Hex/Unicode to prevent ANY non-printable characters
K_DEBT = "\u05d7\u05d5\u05d1 \u05db\u05d5\u05dc\u05dc" # חוב כולל
M_HI = "\u05d4\u05d9" # הי
M_MEET = "\u05de\u05e4\u05d2\u05e9\u05d9\u05dd" # מפגשים
M_TOTAL = "\u05e1\u05d4\"\u05db \u05dc\u05ea\u05e9\u05dc\u05d5\u05dd" # סהכ לתשלום

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files.get('file')
        if f:
            try:
                ‏# הקובץ של אירית הוא CSV שמפריד עם פסיקים אבל יש בו טקסט חופשי
                df = pd.read_csv(f, header=None, encoding='utf-8-sig', sep=',', engine='python')
                
                summary = []
                curr = None

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist() if pd.notna(val)]
                    row_str = " ".join(row_list)

                    # זיהוי שם מטופל לפי השורות עם המקפים: "-------------- אסף בוקצין--------------"
                    if "--------------" in row_str:
                        # מחלץ את הטקסט שבין המקפים
                        name_match = re.search(r'-+\s*(.*?)\s*-+', row_str)
                        if name_match:
                            raw_name = name_match.group(1)
                            # אם זה לא שורת הפירוט, זה השם
                            if "\u05e4\u05d9\u05e8\u05d5\u05d8" not in raw_name: # "פירוט"
                                name = raw_name.strip()
                                if name and (not curr or name != curr['f']):
                                    curr = {'f': name, 's': name.split()[0], 'd': "0", 'dt': []}
                                    summary.append(curr)

                    # זיהוי תאריך בעמודה הראשונה
                    v0 = str(row[0]).strip()
                    if re.match(r'\d{1,2}/\d{1,2}/\d{4}', v0) and curr:
                        curr['dt'].append(v0)

                    # זיהוי סכום - מופיע בשורה שמתחת ל"חוב כולל"
                    if K_DEBT in row_str and curr:
                        if i + 1 < len(df):
                            next_row = [str(x) for x in df.iloc[i+1].tolist()]
                            for val in next_row:
                                num = re.sub(r'[^\d.]', '', val)
                                if num and float(num) > 10:
                                    curr['d'] = str(int(float(num)))
                                    break

                # בניית המייל
                body = "Monthly Billing Summary:\n\n"
                valid_count = 0
                for p in summary:
                    if p['dt'] and p['d'] != "0":
                        valid_count += 1
                        body += f"{p['f']}:\n"
                        body += f"{M_HI} {p['s']}, {len(p['dt'])} {M_MEET}: {', '.join(p['dt'])}\n"
                        body += f"{M_TOTAL}: {p['d']} NIS\n\n---\n\n"

                if valid_count > 0:
                    requests.post("https://api.mailjet.com/v3.1/send", auth=(AK, SK), json={
                        'Messages': [{'From': {'Email': S, 'Name': 'Irit'}, 
                                     'To': [{'Email': e} for e in R], 
                                     'Subject': 'Billing Report', 'TextPart': body}]
                    })
                    return f"<h1>Success! Sent {valid_count} summaries.</h1>"
                return "<h1>No data found.</h1>"

            except Exception as e:
                return f"<h1>Error: {str(e)}</h1>"
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
