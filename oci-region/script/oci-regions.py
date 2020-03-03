# coding: utf-8

# OCI - Region Subscription
# Written by: Florian Bonneville
# Version 1.0 - february 5th 2019

import oci
import csv
import datetime
import os

from oci.signer import Signer
from modules.mod_identity import *
from modules.mod_region import *

red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'
yellow = lambda text: '\033[0;33m' + text + '\033[0m'

###########  -Begin Config- ###########

# specify your config file profile name and path
# Both are not needed if use_instance_principal = 'TRUE'
profile = "DEFAULT"
configfile = "/home/opc/.oci/config"

# set 'TRUE' to use instance principal authentication instead of config file
# specify your tenant OCID
use_instance_principal = 'FALSE'
tenancy_id_instance_principal = "ocid1.tenancy.oc1..aaaaaa..."

# specify path & name for your report
region_report = "/home/opc/Region_report.csv"
errors_log = "/home/opc/Region_errors.log"

###########  -End Config- ###########

now = datetime.datetime.today()
now = now.strftime("%Y-%m-%d")
print(now)

# setup region report file
with open(region_report, mode='w') as csv_file:
    fieldnames = ['Profile', 'Region_Name', 'Region_Code', 'Region_Status', 'Is_Home_Region', 'Date']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

# setup errors report file
with open(errors_log, mode='w') as err:
	err.close()

### setup authentication method ###

configfile = os.path.expanduser(configfile) # In case tilde (~) character is use in path

if use_instance_principal == 'TRUE':
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    config = {}
    tenancy_id = tenancy_id_instance_principal
    
else:

    config = oci.config.from_file(configfile, profile)
    tenancy_id = config['tenancy']
    
    signer = Signer(
        tenancy = config['tenancy'],
        user = config['user'],
        fingerprint = config['fingerprint'],
        private_key_file_location = config['key_file'],
        pass_phrase = config['pass_phrase']
    )

print("\n===========================[ Login check ]=============================")
login(config, signer,use_instance_principal)

if use_instance_principal == 'TRUE':
    object = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    tenant_name = object.get_namespace().data
    print(tenant_name)
else:
    object = oci.object_storage.ObjectStorageClient(config=config)
    tenant_name = object.get_namespace().data
    print(tenant_name)

# call function	
set_regions(config, signer, use_instance_principal, tenant_name, tenancy_id, region_report, now, errors_log)

# delete errors log file if no error recorded.
with open(errors_log, 'r') as readfile:
	has_char = readfile.read(1)
	readfile.close()
if not has_char:
    os.remove(errors_log)
    print("\n==========================={ Log files }=============================")
    print(green("No error found, " + errors_log + " has been deleted"))
    print(green("read " + region_report + " to check region subscibed"))
    print(yellow("run: column -t -s , " + region_report))

else:
    print("\n==========================={ Log files }=============================")
    print(red("errors found, read: " + errors_log))
    print(green("read " + region_report + " to check region subscibed"))
    print(yellow("run: column -t -s , " + region_report))

print()