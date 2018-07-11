ps -ef | grep start.sh | awk -F ' ' '{print $2}' | xargs kill -9
ps -ef | grep application.py | awk -F ' ' '{print $2}' | xargs kill -9
