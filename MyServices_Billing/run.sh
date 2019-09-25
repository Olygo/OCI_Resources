#!/bin/bash

date > /home/USERNAME/get_balance.txt
echo >> /home/USERNAME/get_balance.txt 
python3.6 /home/USERNAME/get_balance.py >> /home/USERNAME/get_balance.txt

date > /home/USERNAME/get_monthly.txt
echo >> /home/USERNAME/get_monthly.txt
python3.6 /home/USERNAME/get_monthly.py 01-09-2019 30-09-2019 >> /home/USERNAME/get_monthly.txt

date > /home/USERNAME/get_usage.txt
echo >> /home/USERNAME/get_usage.txt
python3.6 /home/USERNAME/get_usage.py 01-09-2019 30-09-2019 >> /home/USERNAME/get_usage.txt

date > /home/USERNAME/get_CompCost.txt
echo >> /home/USERNAME/get_CompCost.txt
python3.6 /home/USERNAME/get_CompCost.py 01-09-2019 30-09-2019 >> /home/USERNAME/get_CompCost.txt