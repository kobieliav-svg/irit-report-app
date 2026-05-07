import Flask, render_template, request
import pandas as pd
import requests
import re

app = Flask(__name__)

# --- Configuration ---
AK = '89f6b99bc7bb58943ea4b5e998ab7e4d'
SK = '77445301940d666bcdb044b1f99a3e22'
S = 'kobieliav@gmail.com'
R = ['ishnab@gmail.com', 'kobieliav@gmail.com']

# --- Hebrew Strings (Cleaned from BiDi characters) ---
T_DATE = "תאריך"
T_DEBT = "חוב כולל"
M_TITLE = "שלום אירית, להלן סיכום המפגשים עבור חודש אפריל:"
M_FOR = "עבור: "
M_HI = "הי "
M_P1 = ", במהלך חודש אפריל היו לנו "
M_P2 = " מפגשים בתאריכים: "
M_P3 = "סה\"כ לתשלום: "
M_P4 = " ש\"ח. תודה רבה!"

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        if f:
            try:
                # Load file with flexibility for encoding
                if f.filename.endswith('.csv'):
                    df = pd.read_csv(f, header=None, encoding='utf-8-sig')
                else:
                    df = pd.read_excel(f, header=None)
                
                summary = []
                curr = None

                for i, row in df.iterrows():
                    row_list = [str(val).strip() for val in row.tolist()]
                    
                    # 1. Clean the Name field from dashes and symbols
                    raw_val_4 = str(row[4]).strip() if pd.notna(row[4]) else ""
                    clean_name = re.sub(r'[-/._]{2,}', '', raw_val_4).strip()
                    
                    # 2. Logic to identify Patient Name row
                    # We check if there's a name, it's not the word "Date", and it doesn't look like a date row
                    if clean_name and T_DATE not in clean_name and len(clean_name) > 2:
                        if not ("/" in str(row[0])):
                            curr = {'f': clean_name, 's': clean_name.split()[0], 'd': "0", 'dt': []}
                            summary.append(curr)
                    
                    # 3. Logic to find the Total Debt
                    if any(T_DEBT in s for s in row_list) and curr:
                        val = df.iloc[i + 1][5] if pd.notna(df.iloc[i + 1][5]) else df.iloc[i + 1][6]
                        if pd.notna(val):
                            # Extract only digits and decimal point
                            num_val = re.sub(r'[^\d.]', '', str(val))
                            curr['d'] = num_val if num_val else "0"
                    
                    # 4. Logic to capture meeting dates
                    v0 = str(row[0])
                    if "/" in v0 and any(c.isdigit() for c in v0) and curr:
                        # Ensure it's a meeting row (not summary)
                        if not (pd.notna(row[2]) and str(row[2]).strip()):
                            curr['dt'].append(v0)

                # --- Build Email Body ---
                body = M_TITLE + "\n\n"
                for p in summary:
                    if p['dt'] and p['d'] != "0":
                        body += M_FOR + p['f'] + "\n"
                        body += M_HI + p['s'] + M_p1 + str(len(p['dt'])) + M_P2 + ", ".join(p['dt']) + "\n"
                        body += M_P3 + p['d'] + M_P4 + "\n\n---\n\n"

                # --- Send Mail ---
                requests.post("https://api.mailjet.com/v3.1/send", auth=(AK, SK), json={
                    'Messages': [{'From': {'Email': S, 'Name': 'Irit Billing'}, 
                                 'To': [{'Email': e} for e in R], 
                                 'Subject': 'סיכום חובות חודשי - אפריל', 
                                 'TextPart': body}]
                })
                
                return '<h1>Success! The report was sent.</h1>'
            except Exception as e:
                return f"Error: {str(e)}"
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
