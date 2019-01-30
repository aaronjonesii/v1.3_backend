source bin/activate
FILENAME=$(date +"%m%d%Y.log")
nohup python3 backend/djangoAPI/manage.py runserver 93.188.164.182:8000 >> ../$FILENAME &
