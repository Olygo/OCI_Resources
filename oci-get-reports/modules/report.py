# coding: utf-8

import os
import gzip
import glob
import oci
import pandas as pd
from oci.signer import Signer
from modules.storage import *
from pathlib import Path

# set colors
yellow = lambda text: '\033[0;33m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

def get_reports(config, signer, working_folder, tmp_folder, month, year, prefix_file, use_history, start_after, oci_tname):

  # Check if report folder exists
  report_folder = working_folder + oci_tname
  if not os.path.exists(report_folder):
    os.mkdir(report_folder) 
  
  print (green("\n====> Collecting reports..."))

# collect oci reports
  reporting_namespace = 'bling'
  reporting_bucket = config['tenancy']
  prefix_file = prefix_file
  object_storage = oci.object_storage.ObjectStorageClient(config=config, signer=signer)

# last_file_history allows to start script after the last file already processed. 
  report_bucket_objects = oci.pagination.list_call_get_all_results(object_storage.list_objects,reporting_namespace,reporting_bucket,prefix=prefix_file ,fields='name,size,timeCreated')

  # jump to tmp_folder 
  os.chdir(tmp_folder)

  for o in report_bucket_objects.data.objects:
    print(f"-- {o.name} ===> {o.time_created}")
    object_details = object_storage.get_object(reporting_namespace, reporting_bucket, o.name)
    filename = o.name.rsplit('/', 1)[-1]
    time_created = (o.time_created)
    month_created = time_created.strftime("%m") # get month, 2 digits
    year_created = time_created.strftime("%Y") # get year, 4 digits
    last_file_id = o.name 

    if year_created == year:
      if month_created == month:
        print(f"----> Time period: {month_created} _ {year_created}")
        print(f"Processing: {o.name}")

        # download .gz archive
        with open(tmp_folder + filename, 'wb') as f:
            for chunk in object_details.data.raw.stream(1024 * 1024, decode_content=False):
                f.write(chunk)

        # extract .gz archive
        input = gzip.GzipFile(tmp_folder + filename, 'rb')
        s = input.read()
        input.close()
        output = open(tmp_folder + filename[:-3], 'wb')    # [:-3]  => Remove .gz
        output.write(s)
        output.close()

        # delete .gz archive
        os.remove(tmp_folder + filename)
        f.close()

  # set report name
  monthly_csv = oci_tname + '_' + month + '_' + year + '.csv'

  # use glob pattern matching -> extension = 'csv', save result in csv_list list
  # count csv files extracted
  csv_counter = len(glob.glob1(tmp_folder,"*.csv"))

  if csv_counter > 0:
    print (green(f"\n====> Merging {csv_counter} daily reports..."))
    extension = 'csv'
    csv_list = [i for i in glob.glob('*.{}'.format(extension))]
    
    # merge into a single csv
    monthly = pd.concat([pd.read_csv(f, low_memory=False) for f in csv_list])
    monthly.to_csv( monthly_csv, index=False, encoding='utf-8-sig')
    
    # move final report out of tmp
    monthly_report = str(report_folder) + '/' + str(monthly_csv)
    Path(tmp_folder + monthly_csv).rename(monthly_report)
    
    # cleanup tmp_folder
    print (green("\n====> Removing daily reports..."))
    tmp_list = os.listdir(tmp_folder)

    for filename in tmp_list:
      path_to_csv = os.path.join(tmp_folder, filename)
      os.remove(path_to_csv)

    # record last processed file name for next run.
    last_file_path = os.path.join(report_folder, 'last_file_history')
    with open(last_file_path,'w') as f:
      f.write(last_file_id)  
    f.close()

    # get report & size in GB
    print(f"Report location: {monthly_report}")
    report_size = os.path.getsize(monthly_report) / (1024*1024*1024)
    print(f"Report size: {report_size:.2f} GB")

  else:
    print("Nothing to process")
  
  return monthly_report

