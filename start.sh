#/bin/sh

while [ 1 ]
do
app_run=`ps -ef | grep "python application.py" | grep -v "grep"`
if [ "x""$app_run" = "x" ];then
    nohup python application.py &
    echo "start application" `date`
else
    sleep 30
fi
done
