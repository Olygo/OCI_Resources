import os
import oci
import datetime
import gzip
import glob
import pandas as pd
from oci.signer import Signer
import time

yellow = lambda text: '\033[0;33m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

def get_reports(config, tenancy_id, profile, destination_path, month, use_history, prefix_file):

  reporting_namespace = 'bling'
  report_folder = destination_path + profile

  # Make a directory to receive reports
  if not os.path.exists(report_folder):
      os.mkdir(report_folder)

  print (green("\n[ Collecting reports...]"))
  print()
  reporting_bucket = config['tenancy']
  object_storage = oci.object_storage.ObjectStorageClient(config)
  report_bucket_objects = object_storage.list_objects(reporting_namespace, reporting_bucket, prefix=prefix_file, fields=['timeCreated'])

  for o in report_bucket_objects.data.objects:   
    object_details = object_storage.get_object(reporting_namespace, reporting_bucket, o.name)
    filename = o.name.rsplit('/', 1)[-1]

    time_created = (o.time_created)
    month_created = time_created.strftime("%m") # get month, 2 digits
    year_created = time_created.strftime("%Y") # get year, 4 digits
      
    if month_created == month:

      print(f"----> Time period: {month_created} _ {year_created}")
      print(f"Downloading {o.name}")
      with open(report_folder + '/' + filename, 'wb') as f:
          for chunk in object_details.data.raw.stream(1024 * 1024, decode_content=False):
              f.write(chunk)

      print(f"Extracting {o.name}")  
      input = gzip.GzipFile(report_folder + '/' + filename, 'rb')
      s = input.read()
      input.close()
      output = open(report_folder + '/' + filename[:-3], 'wb')    # [:-3]  => Remove .gz
      output.write(s)
      output.close()
      print(f"Deleting {o.name}")
      print()
      os.remove(report_folder + '/' + filename)

  f.close()

  Monthly_csv = month + '_' + year_created + '_' + profile + '.csv'
  your_report = str(report_folder) + '/' + str(Monthly_csv)
  print(f"your_report is {your_report}")
  if os.path.exists(your_report):
    print("EXISTING REPORT FOUND...")
    os.remove(your_report)
    print("WAIT")
    time.sleep(15)

  print(f"[ CSV files in {report_folder} ]")
  print()

  #use glob pattern matching -> extension = 'csv'
  #save result in list -> all_filenames

  os.chdir(report_folder)

  #Count files csv
  csv_counter = len(glob.glob1(report_folder,"*.csv"))

  if csv_counter > 1:
    print (green("\n[ Merging daily reports...]"))
    print()
    print(f"local csv files to merge: {csv_counter}")
    extension = 'csv'
    all_filenames = [i for i in glob.glob('*.{}'.format(extension))]

    for filename in all_filenames:
        if profile in filename:
          all_filenames.remove(filename)

    for filename in all_filenames:
        Monthly_csv = month + '_' + year_created + '_' + profile + '.csv'
        Monthly = pd.concat([pd.read_csv(f, low_memory=False) for f in all_filenames ])
        Monthly.to_csv( Monthly_csv, index=False, encoding='utf-8-sig')
    
    print (green("\n[ Removing daily reports...]"))
    print()
    csv_in_directory = os.listdir(report_folder)
    filtered_files = [file for file in csv_in_directory if file.endswith(".csv")]
    
    for filename in filtered_files:
      print()
      if profile not in filename:
        path_to_csv = os.path.join(report_folder, filename)
        os.remove(path_to_csv)
  else:
    print("no files to merge")