# coding: utf-8

# OCI - Controls
# Written by: Florian Bonneville
# Version 1.0 - february 5th 2019

import oci
import csv
import datetime
import configparser
import os

from oci.signer import Signer
from modules.mod_identity import *
from modules.mod_autonomous import *
from modules.mod_compute import *
from modules.mod_database import *
from modules.mod_storage import *

black = lambda text: '\033[0;30m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'
yellow = lambda text: '\033[0;33m' + text + '\033[0m'
blue = lambda text: '\033[0;34m' + text + '\033[0m'
magenta = lambda text: '\033[0;35m' + text + '\033[0m'
cyan = lambda text: '\033[0;36m' + text + '\033[0m'
white = lambda text: '\033[0;37m' + text + '\033[0m'

###########  -Begin Config- ###########

# specify your config file profile name and path
# Both are not needed if use_instance_principal = 'TRUE'
profile = "DEFAULT"
configfile = '/home/opc/CloudAccounts/config/configSPEC'

# set 'TRUE' to use instance principal authentication instead of config file
# specify your tenant OCID
use_instance_principal = 'FALSE'
tenancy_id_instance_principal = "ocid1.tenancy.oc1..aaaaaa..."

#Specify path & name for your reports WITHOUT EXTENSION (automatically added)
tags_report = "/home/opc/Tags_Report"
licenses_report = "/home/opc/Licenses_Report"
errors_log = "/home/opc/errors_log"

# Set top level compartment OCID to filter on a Compartment
# Tenancy OCID will be set if null.
top_level_compartment_id = ''

# List compartment names to exclude
excluded_compartments = ['ManagedCompartmentForPaaS']

# List target regions. All regions will be used if null.
target_region_names = ['eu-frankfurt-1']
#target_region_names = ['eu-frankfurt-1','uk-london-1','eu-amsterdam-1','eu-zurich-1']

# cleanup = "YES" => Resources will be deleted if tag is missing 
# otherwise Resources will be logged only if tag is missing
cleanup = "NO"

TagNamespaces = ['System_Tags', 'Mandatory_Tags']
TagKeys = ['Owner'] 

###########  -End Config- ###########

now = datetime.datetime.today()
now = now.strftime("%Y-%m-%d-%H_%M")
print(now)

if cleanup == "YES":
	tags_report = tags_report + "_" + now + "_" + "cleanup" + ".csv"
	licenses_report = licenses_report + "_" + now + "cleanup" + ".csv"
	errors_log = errors_log + "_" + now  + ".log"

	print(red("All untagged objects will be deleted"))
	print(yellow("Tag Report : " + tags_report))
	print(yellow("Licenses Report : " + licenses_report))

else:
	tags_report = tags_report + "_" + now + "_" + "report" + ".csv"
	licenses_report = licenses_report + "_" + now + "report" + ".csv"
	errors_log = errors_log + "_" + now  + ".log"
	print(green("All untagged objects will be listed"))
	print(yellow("Tag Report : " + tags_report))
	print(yellow("Licenses Report : " + licenses_report))

# Setup Licenses report file
with open(licenses_report, mode='w') as csv_file:
    fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'License_Type', 'Compartment', 'Region', 'Owner']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

# Setup Tags report file
with open(tags_report, mode='w') as csv_file:
    fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

# Setup errors report file
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

print("\n==================================[ Login check ]==================================")
login(config, signer, use_instance_principal)

if use_instance_principal == 'TRUE':
    object = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    tenant_name = object.get_namespace().data
    print(tenant_name)
else:
    object = oci.object_storage.ObjectStorageClient(config=config)
    tenant_name = object.get_namespace().data
    print(tenant_name)

print("\n=================================={ Target regions: }==================================")
all_regions = get_region_subscription_list(config, signer, use_instance_principal, tenancy_id)
target_regions=[]
for region in all_regions:
	if (not target_region_names) or (region.region_name in target_region_names):
		target_regions.append(region)
		print(region.region_name)

print("\n=================================={ Target compartments }==================================")
if not top_level_compartment_id:
	top_level_compartment_id = tenancy_id
	
get_compartments = get_compartment_list(config, signer, use_instance_principal, top_level_compartment_id)
compartments = []
for compartment in get_compartments:
	if compartment.name not in excluded_compartments:
		compartments.append(compartment)
		print(compartment.name)

for region in target_regions:
	print (magenta("\n=========================[ {} @ {} ]=============================".format(region.region_name, profile)))
		
	config["region"] = region.region_name
	region = region.region_name

	# call functions	
	# get_instance_pools(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log)
	# get_instance_configurations(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log)
	# get_dedicated_vm_hosts(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log)
	# get_compute_instances(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log)

	# get_buckets(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log)
	# get_boot_volumes(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log)
	# get_boot_volume_backups(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log)
	# get_block_volumes(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log)
	# get_block_volume_backups(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log)
	# get_custom_images(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log)
	# get_volume_group_backups(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log)
	# get_volume_groups(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log)

	# get_database_instances(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log)
	get_autonomous_instances(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log, TagNamespaces, TagKeys)
	# get_no_byol_databases_licences(config, signer, use_instance_principal, tenant_name, region, compartments, licenses_report, cleanup, now, errors_log)
	# get_no_byol_autonomous_licences(config, signer, use_instance_principal, tenant_name, region, compartments, licenses_report, cleanup, now, errors_log)


# delete errors log file if no error recorded.
with open(errors_log, 'r') as readfile:
	has_char = readfile.read(1)
	readfile.close()
if not has_char:
    os.remove(errors_log)
    print("\n==========================={ Log files }=============================")
    print(green("No error found, " + errors_log + " has been deleted"))
    print(green("read " + tags_report + " to check region subscibed"))
    print(green("read " + licenses_report + " to check region subscibed"))
    print(yellow("run: column -t -s , " + tags_report))
    print(yellow("run: column -t -s , " + licenses_report))

else:
    print("\n==========================={ Log files }=============================")
    print(red("errors found, read: " + errors_log))
    print(green("read " + tags_report + " to check region subscibed"))
    print(green("read " + licenses_report + " to check region subscibed"))
    print(yellow("run: column -t -s , " + tags_report))
    print(yellow("run: column -t -s , " + licenses_report))

print()