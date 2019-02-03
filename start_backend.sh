source bin/activate
FILENAME=$(date +"%m%d%Y.log")
nohup python3 djangoAPI/manage.py runserver 0.0.0.0:8000 >> ../$FILENAME &
