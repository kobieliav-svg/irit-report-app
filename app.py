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

# --- Unicode Strings ---
T_DATE = "\u05ea\u05d0\u05e8\u05d9\u05da" # תאריך
T_DEBT = "\u05d7\u05d5\u05d1 \u05db\u05d5\u05dc\u05dc" # חוב כולל

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files.get('file')
        if f:
            try:
                # טעינה בטוחה
                df = pd.read_csv(f, header=None, encoding='utf-8-sig') if f.filename.endswith('.csv') else pd.read_excel(f, header=None)
                
                summary = []
                curr = None

                for i, row in df.iterrows():
                    # הופך את כל השורה לטקסט אחד
                    row_list = [str(val).strip() for val in row.tolist() if pd.notna(val)]
                    row_str = " ".join(row_list)
                    
                    # 1. חיפוש שם מטופל - אם השורה מכילה טקסט ארוך ואין בה תאריך/מספרים בעמודה הראשונה
                    # אנחנו בודקים את עמודה 4 כעוגן, אבל גם בודקים אם יש שם בשורה
                    potential_name = ""
                    if len(row) > 4 and pd.notna(row[4]):
                        potential_name = re.sub(r'[-/._*]{2,}', '', str(row[4])).strip()

                    # אם מצאנו שם פוטנציאלי והוא לא כותרת
                    if potential_name and len(potential_name) > 2 and T_DATE not in potential_name and "/" not in str(row[0]):
                        curr = {'f': potential_name, 's': potential_name.split()[0], 'd': "0", 'dt': []}
                        summary.append(curr)

                    # 2. זיהוי תאריכים (עמודה 0)
                    v0 = str(row[0])
                    if "/" in v0 and any(c.isdigit() for c in v0) and curr:
                        # שורת מפגש: עמודה 0 היא תאריך, עמודה 1 או 2 בדרך כלל ריקות
                        curr['dt'].append(v0)

                    # 3. זיהוי סכום (חוב כולל)
                    if T_DEBT in row_str and curr:
                        # מחפש את המספר הראשון שמופיע בשורה שאחרי "חוב כולל"
                        next_row = df.iloc[i + 1] if i + 1 < len(df) else row
                        for cell in next_row:
                            cell_str = re.sub(r'[^\d.]', '', str(cell))
                            if cell_str and len(cell_str) >= 2:
                                curr['d'] = cell_str
                                break

                # --- שליחת המייל ---
                valid_count = 0
                body = "סיכום חובות:\n\n"
                for p in summary:
                    if p['dt'] and p['d'] != "0":
                        valid_count += 1
                        body += ‏f"עבור: {p['f']}\nהיו {len(p['dt'])} מפגשים: {', '.join(p['dt'])}\nסה\"כ: {p['d']} ש\"ח\n\n---\n\n"

                if valid_count > 0:
                    requests.post("https://api.mailjet.com/v3.1/send", auth=(AK, SK), json={
                        'Messages': [{'From': {'Email': S, 'Name': 'Irit'}, 'To': [{'Email': e} for e in R], 
                                     'Subject': 'Billing Success', 'TextPart': body}]
                    })
                
                return f"<h1>Success! Sent summaries for {valid_count} patients.</h1>"
            except Exception as e:
                return f"<h1>Error: {str(e)}</h1>"
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
