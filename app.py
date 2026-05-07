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

# --- Unicode Hebrew Keywords ---
T_DATE = "\u05ea\u05d0\u05e8\u05d9\u05da" # תאריך
T_DEBT = "\u05d7\u05d5\u05d1 \u05db\u05d5\u05dc\u05dc" # חוב כולל

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        if f:
            try:
                # טעינה בטוחה של הקובץ
                if f.filename.endswith('.csv'):
                    df = pd.read_csv(f, header=None, encoding='utf-8-sig')
                else:
                    df = pd.read_excel(f, header=None)
                
                summary = []
                curr = None

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    
                    # 1. זיהוי שם המטופל (עמודה 4)
                    raw_name = str(row[4]).strip() if len(row) > 4 and pd.notna(row[4]) else ""
                    # ניקוי קווים (---) שעלולים להופיע בשם
                    clean_name = re.sub(r'[-/._*]{2,}', '', raw_name).strip()
                    
                    # אם זו שורת שם מטופל (יש טקסט, אין תאריך בעמודה 0)
                    if clean_name and T_DATE not in clean_name and "/" not in str(row[0]):
                        if len(clean_name) > 2:
                            curr = {'f': clean_name, 's': clean_name.split()[0], 'd': "0", 'dt': []}
                            summary.append(curr)

                    # 2. זיהוי סכום (חוב כולל)
                    if any(T_DEBT in s for s in row_list) and curr:
                        # בודק את עמודה 5 או 6 כפי שהיה במקור, אך עם ניקוי מספרים
                        val = df.iloc[i + 1][5] if pd.notna(df.iloc[i + 1][5]) else df.iloc[i + 1][6]
                        if pd.notna(val):
                            # משאיר רק מספרים ונקודה עשרונית
                            curr['d'] = re.sub(r'[^\d.]', '', str(val))

                    # 3. זיהוי תאריכי מפגשים
                    v0 = str(row[0])
                    if "/" in v0 and any(c.isdigit() for c in v0) and curr:
                        # מוודא שזו שורת פירוט ולא שורת סיכום (עמודה 2 ריקה)
                        if len(row) > 2 and (not str(row[2]).strip() or str(row[2]) == "nan"):
                            curr['dt'].append(v0)

                # --- בניית גוף המייל ---
                m_title = "שלום אירית, להלן סיכום המפגשים עבור חודש אפריל:"
                body = m_title + "\n\n"
                
                valid_emails = 0
                for p in summary:
                    if p['dt'] and p['d'] != "0":
                        valid_emails += 1
                        body += f"עבור: {p['f']}\n"
                        body += ‏f"הי {p['s']}, במהלך חודש אפריל היו לנו {len(p['dt'])} מפגשים בתאריכים: {', '.join(p['dt'])}\n"
                        body += f"סה\"כ לתשלום: {p['d']} ש\"ח. תודה רבה!\n\n---\n\n"

                # אם לא נמצאו נתונים, שולח התראה כדי שלא ננחש
                if valid_emails == 0:
                    body = ‏"המערכת הופעלה אך לא זוהו נתונים תקינים לשליחה בקובץ ה-CSV."

                # שליחה
                res = requests.post("https://api.mailjet.com/v3.1/send", auth=(AK, SK), json={
                    'Messages': [{'From': {'Email': S, 'Name': 'Irit Billing'}, 
                                 'To': [{'Email': e} for e in R], 
                                 'Subject': 'סיכום חובות חודשי - אפריל', 
                                 'TextPart': body}]
                })
                
                return f"<h1>Success! Sent summaries for {valid_emails} patients.</h1>"

            except Exception as e:
                return f"<h1>Error processing file: {str(e)}</h1>"
    
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
