@echo on

if exist ".env" goto :created

python -m venv .env
.env\Scripts\activate
pip install -r requirements.txt

:created

python -m unittest main.py