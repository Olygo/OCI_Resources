# coding: utf-8

##########################################################################
# oci-dl-reports.py
#
# @author: Florian Bonneville, Oct. 24th 2022
# version: 1.0
#
# DISCLAIMER – This is not an official Oracle application,  It does not supported by Oracle Support.
##########################################################################
# Info:
# this script downloads & extracts your OCI Cost reports into your own bucket for the current month (default) or for a specified month & year (arguments).
#
# optional arguments:
#
#   -auth IP                >   authenticate through OCI Instance_Principal (default)
#   -auth CS                >   authenticate through OCI Cloud Shell
#   -auth CF                >   authenticate through OCI Config file
#   -cf /path_to_file       >   specify config file location if not in default location
#   -p profile_nmae         >   specify which profile to use in the config file if many exists
#   -dest local             >   download into a local folder only, default push to OCI
#   -init True              >   download all reports from the last 6 months
#   -m mm                   >   download reports for month mm (01, 02,...)
#   -y yyyy                 >   download reports for year yyyy (2021, 2022,...)
#   -hist True              >   start analysis from last downloaded file, this reduce script duration
#   -f xxxxxxx              >   start analysis after a specific file name, format: reports/cost-csv/0001000000760749.csv.gz
#   -pr reports/usage-csv   >   download cost reports (reports/cost-csv) or usage reports (reports/usage-csv)
#   -wf /path-to-my-dir     >   reports folder location, default is ~/YOUR_TENANT_NAME_cost_reports/
#   -cp My-Comp-Name        >   specify the compartment name where to store your bucket, default is your root compartment
#   -bn My-Bucket-Name      >   specify the bucket name to store your reports, default is "reports_YOUR_TENANT_NAME"
#   -tag False              >   do not add the date Prefix "YYYYMM" to each report
#   -tree False             >   do not organize reports in date tree: /YEAR/MONTH/DAY/xxxxreport.csv

##########################################################################
# Command line examples:
#
#   default will push the .csv cost reports for the current month into a bucket in your root compartment, using Instance_Principal authentication)
#   python3 ./oci-dl-reports.py
#   
#   authenticate through your oci config file
#   python3 ./oci-dl-reports.py -auth CF -cf ~/.oci/config -p DEFAULT
#   
#   authenticate through oci cloud shell
#   python3 ./oci-dl-reports.py -auth CS 
#   
#   if you want to download all available reports (max 6 months old):
#   python3 ./oci-dl-reports.py -init True
# 
#   download reports for a specific month: 
#   python3 ./oci-dl-reports.py -m 09 -y 2022
#
#   download reports for a specific month into a specific compartment & bucket 
#   python3 ./oci-dl-reports.py -cp COMPARTMENT_NAME -bn BUCKET_NAME -m 09 -y 2022
#
#   download reports locally only & for a specific month
#   python3 ./oci-dl-reports.py -dest Local -m 09 -y 2022
#
#   by defaut a date prefix is added to each report and reports are stored in folder using a date tree i.e 2022/09/01/2022-09-01_0001000001055191-00001.csv, you can disable both prefix taging and tree storage
#   python3 ./oci-dl-reports.py -tag False -tree False
#
##########################################################################
# Prerequisites
#
#   tested on Oracle Linux 7 >
#   sudo yum install python3
#   pip3 install --upgrade pip oci-cli oci --user
#   
##########################################################################

import oci
import datetime
import argparse
from modules.report import *
from modules.init_reports import *
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
parser.add_argument('-auth', default="IP", dest='auth_mode', help='select your authentication mode: IP : Use_Instance_Principal, CF : Use_Config_File , CS : Use_Cloud_Shell', required=False, type=str)
parser.add_argument('-cf', default="~/.oci/config", dest='config_file', help='location of your OCI config file, default is ~/.oci/config', required=False, type=str)
parser.add_argument('-p', default="DEFAULT", dest='profile', help='profile to use in your config file, default is "DEFAULT"', required=False, type=str)
parser.add_argument('-m', default=0, dest='month', help='force a specific month to collect, format: 01 to 12', required=False)
parser.add_argument('-y', default=0, dest='year', help='force a specific year to collect, format: 2018 to 2050', required=False)
parser.add_argument('-hist', default="False", dest='use_history', help='start analysis from last downloaded file, this reduce script duration', required=False, type=str)
parser.add_argument('-f', default="", dest='start_after', help='start analysis after a specific file, format: reports/cost-csv/0001000000760749.csv.gz', required=False, type=str)
parser.add_argument('-pr', default="reports/cost-csv", dest='prefix_file', help='download either cost or usage reports, format: reports/cost-csv or reports/usage-csv', required=False, type=str)
parser.add_argument('-wf', default="default", dest='working_folder', help='reports folder location, default is ~/YOUR_TENANT_NAME_cost_reports/', required=False, type=str)
parser.add_argument('-dest', default="OCI", dest='dest', help='reports location: Local or OCI bucket, format: OCI or Local', required=False, type=str)
parser.add_argument('-cp', default="Root", dest='target_comp', help='define the compartment name to store your bucket, default is your root compartment', required=False, type=str)
parser.add_argument('-bn', default="default", dest='target_bucket', help='define the bucket name to store your reports, default : "reports_YOUR_TENANT_NAME', required=False, type=str)
parser.add_argument('-init', default="False", dest='init_reports', help='download 6 months report history, format: True or False ', required=False, type=str)
parser.add_argument('-tag', default="True", dest='tag_reports', help='add the date Prefix "YYYYMM" to each report, format: True or False', required=False, type=str)
parser.add_argument('-tree', default="True", dest='tree_reports', help='organize reports in tree: /YEAR/MONTH/DAY/xxxxreport.csv, format: True or False', required=False, type=str)

# get arguments
# try:
#     cmd = parser.parse_args()
# except:
#     parser.print_help()
#     print(red(" /!\ -auth argument is required, see help section"))
#     raise SystemExit

cmd = parser.parse_args()
auth_mode = cmd.auth_mode
config_file = cmd.config_file
config_profile = cmd.profile
month = cmd.month
year = cmd.year
use_history = cmd.use_history
start_after = cmd.start_after
prefix_file = cmd.prefix_file
working_folder = cmd.working_folder
dest = cmd.dest
target_comp = cmd.target_comp
target_bucket = cmd.target_bucket
init_reports = cmd.init_reports
tag_reports = cmd.tag_reports
tree_reports = cmd.tree_reports

# set global var
yellow = lambda text: '\033[0;33m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'
months_list = ['01','02','03','04','05','06','07','08','09','10','11','12']
now = datetime.datetime.now()
#started = now.strftime("%d/%m/%Y %H:%M:%S")

# check month & year if specified:
if month != 0:
  if month in months_list:
    month = month
    use_history = 'False'
  else:
    print(red(f"\nInvalid month: {month}, must be integer between: 01 => 12"))
    raise SystemExit
  
  if 2018 <= int((year)) <= 2050:
    year = year
  else:
    print(red(f"\nInvalid year: {year}, must be integer between: 2018 => 2050"))
    raise SystemExit

# if no month specified, use current month & year
else: 
    month = now.strftime("%m")
    year = now.strftime("%Y")

# call authentication: get signer
config, signer = create_signer(auth_mode, config_file, config_profile)
tenancy_id = config["tenancy"]
oci_tname = get_tenancy(tenancy_id, config, signer)
print()

# Set Working Folder 
config_file = path_expander(config_file)        # expand path if tilde (~) used in path
if working_folder == 'default':
  working_folder = '~/' + oci_tname + '_cost_reports/'
working_folder = path_expander(working_folder)  # expand path if tilde (~) used in path
tmp_folder = working_folder + ".tmp/"

# Create folders if don't exist
check_folder(working_folder, output=1)
check_folder(tmp_folder, output=1)

#purge .tmp folder before run
for file in os.listdir(tmp_folder):
    os.remove(os.path.join(tmp_folder, file))

# if OCI storage location
if str.upper(dest) == "OCI":
  # check compartment
  if target_comp == 'Root':
    target_comp_id = tenancy_id
  else:
    target_comp_id = check_compartment(config, signer, tenancy_id, target_comp)

  # check compartment & bucket
  target_bucket = check_bucket(config, signer, target_comp_id, target_bucket, tenancy_id, oci_tname)

if str.upper(init_reports) == 'TRUE':
  print_conf (auth_mode,config_file,config_profile,month,year,use_history,start_after,prefix_file,working_folder,dest,target_comp,target_bucket,init_reports,tag_reports,tree_reports)

  # download 6 months reports history
  get_allreports(config, signer, tmp_folder, prefix_file, target_bucket, working_folder, tenancy_id, tag_reports, tree_reports, dest)

else:
  print_conf (auth_mode,config_file,config_profile,month,year,use_history,start_after,prefix_file,working_folder,dest,target_comp,target_bucket,init_reports,tag_reports,tree_reports)

  # download user-defined reports history
  get_reports(config, signer, working_folder, tmp_folder, month, year, prefix_file, use_history, start_after, target_bucket, tenancy_id, tag_reports, tree_reports, dest)

# print script statistics
if str.upper(dest) == "OCI":
  bucket_info = get_bucket_info(config, signer, target_bucket, tenancy_id)
  print(green(f"\nBucket size: {bucket_info[1]:.2f} GB"))
  print(green(f"Bucket files #: {bucket_info[0]}"))

end = datetime.datetime.now()
ended = end.strftime("%d/%m/%Y %H:%M:%S")
duration = end-now
print(green(f"Execution time: {duration}"))
print()