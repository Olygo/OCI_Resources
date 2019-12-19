#!/bin/bash

date > /home/opc/get_balance.txt
echo >> /home/opc/get_balance.txt 
python3.6 /home/opc/get_balance.py >> /home/opc/get_balance.txt

date > /home/opc/get_monthly.txt
echo >> /home/opc/get_monthly.txt
python3.6 /home/opc/get_monthly.py 01-12-2019 31-12-2019 >> /home/opc/get_monthly.txt

date > /home/opc/get_usage.txt
echo >> /home/opc/get_usage.txt
python3.6 /home/opc/get_usage.py 01-12-2019 31-12-2019 >> /home/opc/get_usage.txt

date > /home/opc/get_CompCost.txt
echo >> /home/opc/get_CompCost.txt
python3.6 /home/opc/get_CompCost.py 01-12-2019 31-12-2019 >> /home/opc/get_CompCost.txt

date > /home/opc/get_TagCost.txt
echo >> /home/opc/get_TagCost.txt
python3.6 /home/opc/get_TagCost.py 01-12-2019 31-12-2019 >> /home/opc/get_TagCost.txt