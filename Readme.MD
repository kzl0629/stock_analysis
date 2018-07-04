1. structure
stock_analysis
|
|
|
|-------------application.py  main entry
|
|
|
|-------------stock.py Dealor get data, Indexor calculator data
|
|
|
|-------------logs
|
|
|
|-------------resource
                 |
                 |
                 |
                 |----config.ini
                 |----stock_code.txt
                 |----stock_detail.txt
                 |----history_data
                 |----filter
                        |
                        |
                        |
                        |-------stock_detail_filter.txt
                        |-------macd_filter.txt
                        |-------kdj_filter.txt
                        |-------all_indexor_filter.txt

2. start application
sh ./start.sh &

3. stop application
ps -ef | grep start.sh | awk -F ' ' '{print $2}' | xargs kill -9
ps -ef | grep application.py | awk -F ' ' '{print $2}' | xargs kill -9
