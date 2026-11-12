"""ER Command Centre - Flask + SQLite educational project.
Demo only: not suitable for real patient records or clinical decision-making.
"""
from datetime import datetime, date
from io import BytesIO, StringIO
import csv
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from openpyxl import Workbook

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'hospital.db'
app = Flask(__name__)
app.secret_key = 'change-this-demo-secret-key'

TRIAGE = {1: 'Critical', 2: 'Emergent', 3: 'Urgent', 4: 'Semi-Urgent', 5: 'Non-Urgent'}
FIELDS = ['name','dob','age','gender','blood','phone','econtact','address','triage','complaint','diagnosis','arrival_mode','doctor','bp_sys','bp_dia','hr','spo2','temp','rr','gcs','weight','glucose','allergies','meds','pmh','surgical','notes','status','ward','insurance','arrival_iso']


def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with connect() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT, patient_code TEXT UNIQUE,
            name TEXT NOT NULL, dob TEXT, age INTEGER, gender TEXT, blood TEXT,
            phone TEXT, econtact TEXT, address TEXT, triage INTEGER NOT NULL,
            complaint TEXT NOT NULL, diagnosis TEXT, arrival_mode TEXT, doctor TEXT,
            bp_sys REAL, bp_dia REAL, hr REAL, spo2 REAL, temp REAL, rr REAL,
            gcs REAL, weight REAL, glucose REAL, allergies TEXT, meds TEXT,
            pmh TEXT, surgical TEXT, notes TEXT, status TEXT DEFAULT 'Waiting',
            ward TEXT, insurance TEXT, arrival_iso TEXT NOT NULL)''')
        count = con.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
        if count == 0:
            demos = [
                ('Priya Sharma','1993-04-12',33,'Female','B+','+91 98765 43210',1,'Chest pain, shortness of breath','Suspected Acute MI','Ambulance','Dr. Rajan Mehta',160,100,110,92,37.2,24,15,'Penicillin','Hypertension','In Treatment','Resus-1'),
                ('Arjun Verma','1985-11-23',40,'Male','O+','+91 97654 32109',2,'RIF pain, vomiting, low-grade fever','Acute Appendicitis','Walk-in','Dr. Sunita Joshi',118,76,98,99,38.1,18,15,'None','Nil','Waiting',''),
                ('Fatima Khan','1952-07-01',74,'Female','A+','+91 96543 21098',3,'Sudden confusion, slurred speech','TIA / Ischaemic Stroke','Ambulance','Dr. Aditya Singh',180,110,88,96,36.9,16,13,'Aspirin','T2DM, HTN','In Treatment','Stroke Bay'),
                ('Rohan Das','2002-03-15',24,'Male','AB-','+91 95432 10987',4,'Laceration right forearm','Soft tissue laceration','Walk-in','Dr. Priya Bose',122,78,82,100,36.6,14,15,'None','Nil','Waiting','Minor Injuries'),
                ('Meera Iyer','1978-09-30',48,'Female','O-','+91 94321 09876',5,'Mild headache, nasal congestion','URTI','Walk-in','Dr. Karthik Rajan',116,72,76,99,37.8,14,15,'Sulfa drugs','Allergic rhinitis','Discharged',''),
            ]
            now = datetime.now()
            for i, d in enumerate(demos):
                arrival = (now.replace(microsecond=0)).isoformat()
                con.execute('''INSERT INTO patients
                    (patient_code,name,dob,age,gender,blood,phone,triage,complaint,diagnosis,arrival_mode,doctor,bp_sys,bp_dia,hr,spo2,temp,rr,gcs,allergies,pmh,status,ward,arrival_iso)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (f'DEMO{i+1:03}', *d, arrival))


def patient_dict(row):
    p = dict(row)
    p['risk'] = risk_score(p)
    p['triage_label'] = TRIAGE.get(p['triage'], 'Unknown')
    p['wait_min'] = max(0, int((datetime.now() - datetime.fromisoformat(p['arrival_iso'])).total_seconds() // 60))
    return p


def risk_score(p):
    """Transparent demo heuristic; it is not a validated medical score."""
    score = {1: 45, 2: 32, 3: 20, 4: 10, 5: 5}.get(int(p.get('triage') or 5), 5)
    def num(k):
        try: return float(p.get(k) or 0)
        except (TypeError, ValueError): return 0
    if num('spo2') and num('spo2') < 94: score += 18
    if num('hr') > 100: score += 10
    if num('temp') > 38.5: score += 7
    if num('gcs') and num('gcs') < 13: score += 18
    if num('bp_sys') > 180 or (num('bp_sys') and num('bp_sys') < 90): score += 10
    return min(100, score)


def get_patients():
    with connect() as con:
        rows = con.execute('SELECT * FROM patients ORDER BY triage ASC, arrival_iso ASC').fetchall()
    return [patient_dict(r) for r in rows]


@app.route('/')
def index():
    patients = get_patients()
    counts = {s: sum(p['status'] == s for p in patients) for s in ['Waiting','In Treatment','Admitted','Discharged']}
    triage_counts = {str(i): sum(p['triage'] == i for p in patients) for i in range(1,6)}
    high_risk = sum(p['risk'] >= 60 for p in patients)
    avg_wait = round(sum(p['wait_min'] for p in patients) / len(patients)) if patients else 0
    return render_template('index.html', patients=patients, counts=counts, triage_counts=triage_counts,
                           high_risk=high_risk, avg_wait=avg_wait, triage=TRIAGE)


@app.post('/patients/add')
def add_patient():
    form = request.form
    required = ['name','dob','gender','triage','complaint']
    if any(not form.get(k, '').strip() for k in required):
        flash('Please complete all required fields.', 'error')
        return redirect(url_for('index') + '#admit')
    try:
        dob = date.fromisoformat(form['dob'])
        age = max(0, (date.today() - dob).days // 365)
        triage_level = int(form['triage'])
        if triage_level not in TRIAGE: raise ValueError
    except ValueError:
        flash('Please enter a valid date of birth and triage level.', 'error')
        return redirect(url_for('index') + '#admit')
    vals = {k: form.get(k, '').strip() for k in FIELDS}
    vals['age'] = age
    vals['triage'] = triage_level
    vals['arrival_iso'] = datetime.now().isoformat(timespec='seconds')
    vals['status'] = vals.get('status') or 'Waiting'
    code = f"ER{datetime.now():%y%m%d%H%M%S%f}"
    cols = ['patient_code'] + FIELDS
    values = [code] + [vals.get(k, '') for k in FIELDS]
    with connect() as con:
        con.execute(f"INSERT INTO patients ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})", values)
    flash(f'Patient {code} registered successfully.', 'success')
    return redirect(url_for('index') + '#patients')


@app.post('/patients/<int:patient_id>/delete')
def delete_patient(patient_id):
    with connect() as con:
        con.execute('DELETE FROM patients WHERE id=?', (patient_id,))
    flash('Patient record deleted.', 'success')
    return redirect(url_for('index') + '#patients')


@app.post('/patients/<int:patient_id>/status')
def update_status(patient_id):
    status = request.form.get('status', 'Waiting')
    if status not in ['Waiting','In Treatment','Admitted','Discharged']:
        flash('Invalid status.', 'error')
    else:
        with connect() as con:
            con.execute('UPDATE patients SET status=? WHERE id=?', (status, patient_id))
        flash('Patient status updated.', 'success')
    return redirect(url_for('index') + '#patients')


@app.route('/api/insights')
def insights():
    pts = get_patients()
    waiting = [p for p in pts if p['status'] == 'Waiting']
    high = sorted([p for p in pts if p['risk'] >= 60], key=lambda p: p['risk'], reverse=True)
    avg_wait = round(sum(p['wait_min'] for p in pts) / len(pts)) if pts else 0
    return jsonify({'total':len(pts), 'waiting':len(waiting), 'high_risk':len(high), 'average_wait':avg_wait,
                    'priority_patients':[{'name':p['name'],'triage':p['triage'],'risk':p['risk']} for p in high],
                    'message': f"There are {len(pts)} patients, {len(waiting)} waiting and {len(high)} flagged high-risk by the demo heuristic. Average recorded wait is {avg_wait} minutes. This is an administrative summary, not clinical advice."})


@app.route('/export/csv')
def export_csv():
    pts = get_patients()
    output = StringIO()
    columns = ['patient_code','name','age','gender','blood','triage','triage_label','complaint','diagnosis','status','doctor','phone','spo2','hr','temp','wait_min','risk']
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    writer.writeheader(); writer.writerows(pts)
    data = BytesIO(('\ufeff' + output.getvalue()).encode('utf-8')); data.seek(0)
    return send_file(data, mimetype='text/csv', as_attachment=True, download_name='ER_patients.csv')


@app.route('/export/excel')
def export_excel():
    pts = get_patients()
    wb = Workbook(); ws = wb.active; ws.title = 'Patients'
    cols = ['Patient ID','Name','Age','Gender','Blood Group','Triage','Triage Label','Complaint','Diagnosis','Status','Doctor','Phone','SpO2','Heart Rate','Temperature','Wait (min)','Demo Risk Score']
    ws.append(cols)
    for p in pts:
        ws.append([p['patient_code'],p['name'],p['age'],p['gender'],p['blood'],p['triage'],p['triage_label'],p['complaint'],p['diagnosis'],p['status'],p['doctor'],p['phone'],p['spo2'],p['hr'],p['temp'],p['wait_min'],p['risk']])
    for cell in ws[1]: cell.font = cell.font.copy(bold=True)
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = min(28, max(14, max(len(str(c.value or '')) for c in col) + 2))
    summary = wb.create_sheet('Summary')
    summary.append(['Metric','Value'])
    summary.append(['Total patients',len(pts)])
    for status in ['Waiting','In Treatment','Admitted','Discharged']:
        summary.append([status,sum(p['status']==status for p in pts)])
    summary.append(['High demo risk (60+)',sum(p['risk']>=60 for p in pts)])
    buf = BytesIO(); wb.save(buf); buf.seek(0)
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='ER_Command_Centre.xlsx')


@app.post('/patients/clear')
def clear_patients():
    with connect() as con: con.execute('DELETE FROM patients')
    flash('All patient records cleared.', 'success')
    return redirect(url_for('index'))


init_db()
if __name__ == '__main__':
    app.run(debug=True)
