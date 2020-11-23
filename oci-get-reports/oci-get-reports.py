"""  
requirements:
 sudo yum install python3
 pip3 install --upgrade pip --user
 pip3 install oci-cli --user
 pip3 install pandas --user

usage:
default call will download only the cost reports for the current month
 python3 ./get_reports.sh

to download reports for a specific month, specify the month (i.e. 01 02 03 04 05 06 07 08 09 10 11 12) 
python3 ./get_reports.sh 05
tenant section in your config file must be your tenant name
"""

import os
import sys
import oci
import datetime
import configparser
from oci.signer import Signer
from modules.report import get_reports
from modules.identity import login, get_compartment_list, clear

#---------------------------{ Config Section Start }---------------------------#

# Update these values
destination_path = '/home/opc/reports/'
configfile = "/home/opc/.oci/config"

# Download all usage and cost files. You can comment out based on the specific need:
# prefix_file = ""                     #  To donwnload cost and usage files
prefix_file = "reports/cost-csv"   #  To download cost only
# prefix_file = "reports/usage-csv"  #  To download usage only

#---------------------------{ Config Section End }---------------------------#

yellow = lambda text: '\033[0;33m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

clear()

# Check if report folder exists
if not os.path.exists(destination_path):
  os.mkdir(destination_path)

config = configparser.ConfigParser()
config.read(configfile)

# get current date
now = datetime.datetime.today()
month_list = ['01','02','03','04','05','06','07','08','09','10','11','12']

# if user specifies a valid month in argument:
if len(sys.argv) > 1:
  if sys.argv[1] in month_list:  
      month = sys.argv[1]
      use_history = 'FALSE'
  else:
    print(red("Invalid month format: " + sys.argv[1]))
    print(red("month format must be: 01 02 03 04 05 06 07 08 09 10 11 12"))
    quit()
else: # if user doesn't specify a month in argument, script uses current month
    month = now.strftime("%m")
    print(f"Current month #: {month}")
    use_history = 'TRUE'

# For each tenant/profile in the config file
for profile in config.sections():
  print(f"Working on: {profile}")
  print()
  config = oci.config.from_file(configfile, profile)
  tenancy_id = config['tenancy']
      
  signer = Signer(
                  tenancy = config['tenancy'],
                  user = config['user'],
                  fingerprint = config['fingerprint'],
                  private_key_file_location = config['key_file'],
                  pass_phrase = config['pass_phrase']
                  )

  print(f"===========================[ Login check {profile} ]===========================")
  login(config, signer)

  get_reports(config, tenancy_id, profile, destination_path, month, use_history, prefix_file)