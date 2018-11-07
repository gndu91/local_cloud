@echo on

if exist ".env" goto :created

python -m venv .env
.env\Scripts\activate
pip install -r requirements.txt

:created

.env\Scripts\python.exe -m unittest main.py