from flask import Flask, render_template, request
import pandas as pd
import requests
import re

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
        f = request.files.get('file')
        if f:
            try:
                # טעינה בטוחה
                if f.filename.endswith('.csv'):
                    df = pd.read_csv(f, header=None, encoding='utf-8-sig')
                else:
                    df = pd.read_excel(f, header=None)
                
                summary = []
                curr = None

                for i, row in df.iterrows():
                    # הופך את השורה לטקסט לחיפוש מילות מפתח
                    row_str = " ".join([str(val) for val in row.values if pd.notna(val)])
                    
                    # 1. זיהוי שם מטופל בעמודה E (אינדקס 4)
                    val_e = str(row[4]).strip() if len(row) > 4 and pd.notna(row[4]) else ""
                    # ניקוי תווים מיוחדים
                    clean_name = re.sub(r'[-/._*]{2,}', '', val_e).strip()
                    
                    # אם מצאנו שם בעמודה E והוא לא מכיל את המילה "תאריך"
                    if clean_name and len(clean_name) > 2 and T_DATE not in clean_name:
                        # וודא שזו לא שורה של תאריך (עמודה A לא מכילה /)
                        if "/" not in str(row[0]):
                            curr = {
                                'f': clean_name,
                                's': clean_name.split()[0],
                                'd': "0",
                                'dt': []
                            }
                            summary.append(curr)

                    # 2. זיהוי תאריכים בעמודה A (אינדקס 0)
                    v0 = str(row[0]).strip()
                    if "/" in v0 and any(c.isdigit() for c in v0) and curr:
                        # מוודא שזו שורת מפגש (עמודה B בדרך כלל ריקה)
                        val_b = str(row[1]).strip() if len(row) > 1 else ""
                        if val_b == "" or val_b == "nan":
                            curr['dt'].append(v0)

                    # 3. זיהוי סכום (חוב כולל)
                    if T_DEBT in row_str and curr:
                        # מחפש את המספר בשורה מתחת בעמודה F או G (5 או 6)
                        search_row = df.iloc[i + 1] if i + 1 < len(df) else row
                        for cell in search_row:
                            num_val = re.sub(r'[^\d.]', '', str(cell))
                            if num_val and len(num_val) >= 2:
                                curr['d'] = num_val
                                break

                # --- שליחת המייל ---
                valid_count = 0
                email_body = "שלום אירית, להלן סיכום המפגשים:\n\n"
                
                for p in summary:
                    if p['dt'] and p['d'] != "0":
                        valid_count += 1
                        email_body += f"עבור: {p['f']}\n"
                        email_body += ‏f"הי {p['s']}, היו לנו {len(p['dt'])} מפגשים בתאריכים: {', '.join(p['dt'])}\n"
                        email_body += f"סה\"כ לתשלום: {p['d']} ש\"ח\n\n---\n\n"

                if valid_count > 0:
                    requests.post("https://api.mailjet.com/v3.1/send", auth=(AK, SK), json={
                        'Messages': [{'From': {'Email': S, 'Name': 'Irit Billing'}, 
                                     'To': [{'Email': e} for e in R], 
                                     'Subject': 'סיכום חובות חודשי', 
                                     'TextPart': email_body}]
                    })
                    return f"<h1>Success! Sent summaries for {valid_count} patients.</h1>"
                else:
                    return "<h1>No valid data found to send.</h1>"

            except Exception as e:
                return f"<h1>Error: {str(e)}</h1>"
    
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
