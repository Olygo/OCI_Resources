# coding: utf-8

##########################################################################
# oci-get-reports.py
#
# @author: Florian Bonneville, May 1st 2022
#
# Supports Python 3
#
# DISCLAIMER – This is not an official Oracle application,  It does not supported by Oracle Support.
##########################################################################
# Info:
# get OCI Cost or Usage reports for current month (default) or specified month & year (arguments), then merge into a single csv file.
#
##########################################################################
# Application Command line parameters
#
#   by default downloads cost reports for the current month
#   python3 ./oci-get-reports.py
#   
#   download reports for a specific month: 
#   python3 ./oci-get-reports.py 05 2022
#
##########################################################################
# Prerequisites
#
#   sudo yum install python3
#   pip3 install --upgrade pip oci-cli oci pandas --user
#   
##########################################################################

import os
import oci
import datetime
import time
import argparse
from modules.report import *
from modules.identity import *
from modules.storage import *
from modules.compartments import *

##########################################################################
# Pre Main
##########################################################################

# clear screen
clear()

# Get command line parser
parser = argparse.ArgumentParser()
parser.add_argument('-cf', default="~/.oci/config", dest='config_file', help='Config file location', required=False, type=str)
parser.add_argument('-p', default="DEFAULT", dest='profile', help='Profile in config file', required=False, type=str)
parser.add_argument('-ip', default=False, dest='instance_principals', help='Authenticate with instance principalx, true, false ', required=False, type=str)
parser.add_argument('-cs', default=False, dest='cloud_shell', help='Authenticate with cloud shell, true, false ', required=False, type=str)
parser.add_argument('-m', default='00', dest='month', help='month to collect', required=False)
parser.add_argument('-y', default='0000', dest='year', help='year to collect', required=False)
parser.add_argument('-hist', default='False', dest='use_history', help='start analysis after last processed file', required=False, type=str)
parser.add_argument('-f', default='', dest='start_after', help='start analysis after file, i.e. reports/cost-csv/0001000000760749.csv.gz', required=False, type=str)
parser.add_argument('-pr', default="reports/cost-csv", dest='prefix_file', help='reports/cost-csv or reports/usage-csv ', required=False, type=str)
parser.add_argument('-wf', default="~/oci_reports/", dest='working_folder', help='Reports folder location ', required=False, type=str)
parser.add_argument('-oci ', default="True", dest='object_storage', help='Store in oci object storage : True or False ', required=False, type=str)
parser.add_argument('-cp', default="oci_cost_reports", dest='target_comp', help='Target compartment name ', required=False, type=str)
parser.add_argument('-bn', default="oci_cost_reports", dest='target_bucket', help='Target bucket name ', required=False, type=str)

### VIRER LE HIST QUAND ON UTILISE ARGUMENTS -m et -y
## Mettre dans un log les noms de fichiers avec les dates afférentes pour gagner du temps lors des parsing suivant ?
# plus facile de restart ainsi depuis un point donné en fonction de la période recherchée.


# get arguments
cmd = parser.parse_args()
config_file = cmd.config_file
config_profile = cmd.profile
is_delegation_token = cmd.cloud_shell
is_instance_principals = cmd.instance_principals
month = cmd.month
year = cmd.year
use_history = cmd.use_history
start_after = cmd.start_after
prefix_file = cmd.prefix_file
working_folder = cmd.working_folder
object_storage = cmd.object_storage
target_comp = cmd.target_comp
target_bucket = cmd.target_bucket

# set colors
yellow = lambda text: '\033[0;33m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

# In case tilde (~) used in paths
config_file = path_expander(config_file)
working_folder = path_expander(working_folder)
tmp_folder = working_folder + ".tmp/"

# Create folders if don't exist
check_folder(working_folder)
check_folder(tmp_folder)

# datetime object containing current date and time
now = datetime.datetime.now()
started = now.strftime("%d/%m/%Y %H:%M:%S")
#run_date = now.strftime("%d-%m-%Y_%H-%M")

# set months
months_list = ['01','02','03','04','05','06','07','08','09','10','11','12']

# if month & year specified:
if month != '00':
  if month in months_list:  
      month = month
      use_history = 'False'
  else:
    print(f"\nInvalid month: {month}, must be: 01 => 12")
    raise SystemExit
  
  if year != '0000':
    if 2018 <= int((year)) <= 2050:
        year = year
  else:
    print(f"\nInvalid year: {year}, must be: 2018 => 2050")
    raise SystemExit

else: # if no month specified, use current month & year
    month = now.strftime("%m")
    print(f"Current month #: {month}")
    year = now.strftime("%Y")
    print(f"Current year #: {year}")


# call authentication: get signer
config, signer = create_signer(config_file, config_profile, is_instance_principals, is_delegation_token)
tenancy_id = config["tenancy"]
oci_tname = get_tenancy(tenancy_id, config, signer)

print(f"OCI config file location: {config_file}")
print(f"OCI config profile location: {config_profile}")
print(f"\nReporting folder location: {working_folder}")

time.sleep(3)

if str.upper(object_storage) == 'TRUE':

  # call compartment function
  target_comp_id = check_compartment(config, signer, tenancy_id, target_comp)
  
  # call bucket function
  check_bucket(config, signer, target_comp_id, target_bucket, tenancy_id)

# call reports function
monthly_report = get_reports(config, signer, working_folder, tmp_folder, month, year, prefix_file, use_history, start_after, oci_tname)

# if oci argument submitted, upload to object storage
if str.upper(object_storage) == 'TRUE':

  # call upload function
  updload_file(config, signer, target_bucket, monthly_report, tenancy_id, working_folder)
          
end = datetime.datetime.now()
ended = end.strftime("%d/%m/%Y %H:%M:%S")
duration = end-now
print(f"\nExecution time: {duration}")
print()