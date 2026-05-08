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

# Month mapping for Hebrew
HEB_MONTHS = {
    1: "\u05d3\u05e6\u05de\u05d1\u05e8", 2: "\u05e4\u05d1\u05e8\u05d5\u05d0\u05e8", 3: "\u05de\u05e8\u05e5",
    4: "\u05d0\u05e4\u05e8\u05d9\u05dc", 5: "\u05de\u05d0\u05d9", 6: "\u05d9\u05d5\u05e0\u05d9",
    7: "\u05d9\u05d5\u05dc\u05d9", 8: "\u05d0\u05d5\u05d2\u05d5\u05e1\u05d8", 9: "\u05e1\u05e4\u05d8\u05de\u05d1\u05e8",
    10: "\u05d0\u05d5\u05e7\u05d8\u05d5\u05d1\u05e8", 11: "\u05e0\u05d5\u05d1\u05de\u05d1\u05e8", 12: "\u05d3\u05e6\u05de\u05d1\u05e8"
}

# Unicode Pieces
U_FOR = "\u05e2\u05d1\u05d5\u05e8: " # עבור:
U_HI = "\u05d4\u05d9 " # הי
U_DURING = " \u05d1\u05de\u05d4\u05dc\u05da \u05d7\u05d5\u05d3\u05e9 " # במהלך חודש
U_HAVE = " \u05d4\u05d9\u05d5 \u05dc\u05e0\u05d5 " # היו לנו
U_MEET = " \u05de\u05e4\u05d2\u05e9\u05d9\u05dd \u05d1\u05ea\u05d0\u05e8\u05d9\u05db\u05d9\u05dd: " # מפגשים בתאריכים:
U_PAY = "\u05e1\u05d4\"\u05db \u05dc\u05ea\u05e9\u05dc\u05d5\u05dd: " # סה"כ לתשלום:
U_NIS = " \u05e9\"\u05d7. \u05ea\u05d5\u05d3\u05d4 \u05e8\u05d1\u05d4!" # ש"ח. תודה רבה!

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files.get('file')
        if f:
            try:
                df = pd.read_csv(f, header=None, encoding='utf-8-sig', sep=',', engine='python')
                summary = []
                curr = None
                detected_month = ""

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist() if pd.notna(val)]
                    row_str = " ".join(row_list)

                    if "--------------" in row_str:
                        match = re.search(r'-+\s*(.*?)\s*-+', row_str)
                        if match:
                            raw_name = match.group(1)
                            if "\u05e4\u05d9\u05e8\u05d5\u05d8" not in raw_name:
                                name = raw_name.strip()
                                if name and (not curr or name != curr['f']):
                                    curr = {'f': name, 's': name.split()[0], 'd': "0", 'dt': []}
                                    summary.append(curr)

                    v0 = str(row[0]).strip()
                    if re.match(r'\d{1,2}/\d{1,2}/\d{4}', v0) and curr:
                        curr['dt'].append(v0)
                        # זיהוי החודש מהתאריך הראשון שנמצא בקובץ
                        if not detected_month:
                            try:
                                m_num = int(v0.split('/')[1])
                                detected_month = HEB_MONTHS.get(m_num, "")
                            except: pass

                    if "\u05d7\u05d5\u05d1 \u05db\u05d5\u05dc\u05dc \u05de\u05d8\u05d5\u05e4\u05dc" in row_str and curr:
                        if i + 1 < len(df):
                            debt_val = str(df.iloc[i+1][5])
                            num = re.sub(r'[^\d.]', '', debt_val)
                            if num:
                                curr['d'] = str(int(float(num)))

                full_body = ""
                valid_count = 0
                month_text = detected_month if detected_month else "\u05d0\u05e4\u05e8\u05d9\u05dc" # ברירת מחדל אפריל

                for p in summary:
                    if p['dt'] and p['d'] != "0":
                        valid_count += 1
                        full_body += U_FOR + p['f'] + "\n"
                        full_body += U_HI + p['s'] + U_DURING + month_text + U_HAVE + str(len(p['dt'])) + U_MEET + ", ".join(p['dt']) + "\n"
                        full_body += U_PAY + p['d'] + U_NIS + "\n\n---\n\n"

                if valid_count > 0:
                    requests.post("https://api.mailjet.com/v3.1/send", auth=(AK, SK), json={
                        'Messages': [{'From': {'Email': S, 'Name': 'Irit'}, 
                                     'To': [{'Email': e} for e in R], 
                                     'Subject': '\u05e1\u05d9\u05db\u05d5\u05dd \u05d7\u05d5\u05d1\u05d5\u05ea', 'TextPart': full_body}]
                    })
                    return f"<h1>Success! Sent {valid_count} summaries for {month_text}.</h1>"
                return "<h1>No data found.</h1>"

            except Exception as e:
                return f"<h1>Error: {str(e)}</h1>"
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
