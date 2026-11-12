# ER Command Centre — Python / Flask

A VS Code-ready conversion of the uploaded ER Command Centre project into a Python Flask application with a SQLite database.

## Features
- Dashboard with patient totals, status counts, average waiting time and triage distribution
- Patient registration with required-field validation and age calculation
- SQLite persistence (`hospital.db` is created automatically)
- Patient search, status updates and delete action
- Local rule-based risk indicator and summary endpoint (`/api/insights`)
- Excel workbook export (`Patients` and `Summary` sheets) and CSV export
- Responsive dark interface
- Demo records are inserted automatically the first time the database is created

## Requirements
- Python 3.10 or newer
- Visual Studio Code
- Python extension for VS Code

## Run in VS Code (Windows)
1. Extract/open this folder in VS Code: **File → Open Folder → ER_Command_Centre**.
2. Open Terminal → New Terminal.
3. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
4. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt terminal and run:
   ```cmd
   .venv\Scripts\activate.bat
   ```
5. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
6. Start the app:
   ```bash
   python app.py
   ```
7. Open **http://127.0.0.1:5000** in your browser.

## Run on macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000.

## Project structure
```text
ER_Command_Centre/
├── app.py                 # Flask routes, validation, SQLite and exports
├── hospital.db            # Created automatically on first run (not included)
├── requirements.txt      # Python dependencies
├── README.md              # Setup instructions
├── .gitignore
├── templates/
│   └── index.html         # Main web interface (Jinja template)
└── static/
    ├── style.css          # Styling and responsive layout
    └── app.js              # Search and insights UI behaviour
```

## Important safety note
This is an educational/demo application. The risk score is a simple, unvalidated rule-based indicator and must not be used for diagnosis, triage decisions or patient care. Do not enter real patient-identifiable or confidential health information. Before any real deployment, obtain clinical, security, privacy and regulatory review; add authentication, authorization, audit logs, encryption, backups and secure configuration. Change the Flask secret key before deployment. The included demo records are fictional.
