# coding: utf-8

import os
import gzip
import oci
from oci.signer import Signer
from modules.storage import *

# set colors
yellow = lambda text: '\033[0;33m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

def get_reports(config, signer, working_folder, tmp_folder, month, year, prefix_file, use_history, start_after, target_bucket, tenancy_id, tag_reports, tree_reports, dest):
  
  print(yellow(f"  -Collected reports: M:{month} Y:{year}"))
  time.sleep(10) # display info for 10sec.
  
  # get last_file_id if specified or if exists from previous run
  if start_after:
    last_file_id = start_after
    print(f'starting analysis after file: {last_file_id}')
  else:
    if str.upper(use_history) == 'FALSE':
      last_file_id = ''
    else:
      try:
        last_file_path = os.path.join(working_folder, 'last_file_history')

        with open(last_file_path,'r') as f:
          last_file_id = f.read().split("\n") # .strip => remove new line chars => /n
          f.close()
          last_file_id = last_file_id[0]

        print(f'starting analysis from {last_file_id}')

      except:
        last_file_id = ''
  
  print (green("\n====> Collecting reports..."))

# collect oci reports
  reporting_namespace = 'bling'
  reporting_bucket = config['tenancy']
  prefix_file = prefix_file
  object_storage = oci.object_storage.ObjectStorageClient(config=config, signer=signer)

# last_file_history allows to start script after the last file already processed. 
  if last_file_id:
    report_bucket_objects = oci.pagination.list_call_get_all_results(object_storage.list_objects,reporting_namespace,reporting_bucket,prefix=prefix_file ,fields='name,size,timeCreated',start_after=last_file_id)
  else:
    report_bucket_objects = oci.pagination.list_call_get_all_results(object_storage.list_objects,reporting_namespace,reporting_bucket,prefix=prefix_file ,fields='name,size,timeCreated')

  # jump to tmp_folder 
  os.chdir(tmp_folder)

  for o in report_bucket_objects.data.objects:
    print(f"-- {o.name} ===> {o.time_created}")
    object_details = object_storage.get_object(reporting_namespace, reporting_bucket, o.name)
    gz_report = o.name.rsplit('/', 1)[-1]
    time_created = (o.time_created)
    day_created = time_created.strftime("%d") # get month, 2 digits
    month_created = time_created.strftime("%m") # get month, 2 digits
    year_created = time_created.strftime("%Y") # get year, 4 digits
    last_file_id = o.name 

    if year_created == year:
      if month_created == month:
        print(f"----> Time period: {month_created} _ {year_created}")
        print(yellow(f"Processing: {o.name}"))

        # download .gz archive
        with open(tmp_folder + gz_report, 'wb') as gz_file:
            for chunk in object_details.data.raw.stream(1024 * 1024, decode_content=False):
                gz_file.write(chunk)
        gz_file.close()

        # extract .gz archive
        input = gzip.GzipFile(tmp_folder + gz_report, 'rb')
        s = input.read()
        input.close()
        output = open(tmp_folder + gz_report[:-3], 'wb')    # [:-3]  => Remove .gz
        output.write(s)
        output.close()

        for file in os.listdir(tmp_folder):
          if file.endswith(".csv"):
            if str.upper(tag_reports) == 'TRUE':
              tag=str(o.time_created)[0:10] #extract date from file date properties
              newfile = tag + '_' + file
              os.rename (file, newfile)
              file = newfile

            #print(os.path.join(tmp_folder, file))
            file2upload = os.path.join(tmp_folder, file)

        if dest == 'OCI':
          # call upload function
          updload_file(config, signer, target_bucket, file2upload, tenancy_id, day_created, month_created, year_created, tree_reports, tmp_folder)

        else:
          # call move function
          move_file(file2upload, day_created, month_created, year_created, tree_reports, working_folder, tmp_folder, file)

  return