# coding: utf-8

# OCI - Budgets
# This script will collect Tags for main OCI Objects, then it will create an associated budget.
# Written by: Florian Bonneville
# Version 1.0 - march 13 2020

import oci
import csv
import datetime
import configparser
import os

from oci.signer import Signer
from modules.mod_identity import *
from modules.mod_autonomous import *
from modules.mod_compute import *
from modules.mod_network import *
from modules.mod_database import *
from modules.mod_storage import *
from modules.mod_budget import *

black = lambda text: '\033[0;30m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'
yellow = lambda text: '\033[0;33m' + text + '\033[0m'
blue = lambda text: '\033[0;34m' + text + '\033[0m'
magenta = lambda text: '\033[0;35m' + text + '\033[0m'
cyan = lambda text: '\033[0;36m' + text + '\033[0m'
white = lambda text: '\033[0;37m' + text + '\033[0m'

###########  -Begin Config- ###########

# --- Authentication parameters if authentication with Config file --- #
profile = "DEFAULT"					# specify your config file profile name and path
configfile = '/home/opc/.oci/config'

# --- Authentication parameters if authentication with Instance Principal --- #
use_instance_principal = 'FALSE' 									# set 'TRUE' to use instance principal authentication instead of config file
tenancy_id_instance_principal = "ocid1.tenancy.oc1..aaaaaa..."		# specify your tenant OCID 
top_level_compartment_id = ''										# Set top level compartment OCID to filter on a Compartment // Tenancy OCID will be set if null.

# --- Script parameters --- #
excluded_compartments = ['XYZxyz', 'ABCabc']	# List compartment names to exclude
target_region_names = ['eu-frankfurt-1']		# List target regions. All regions will be used if null.
#target_region_names = ['eu-frankfurt-1','uk-london-1','eu-amsterdam-1','eu-zurich-1']

cleanup = 'TRUE'							# If TRUE, the script will delete budget if no corresponding Tag found

myTagNamespace = "System_Tags"				# Specify the name of the TagNamespace where is located the key to look for
myTagKey = "Owner"							# Specify the name of the Key to look for 
excluded_tags = ['logging']					# Tags for which you don't want to create a budget

# --- Budget parameters --- #
threshold_metric = "FORECAST"							# "ACTUAL": alert will trigger based on actual usage // "FORECAST": alert will trigger based on predicted usage
threshold = "95"										# The threshold for triggering the alert expressed as a whole number or decimal value. 
threshold_type = "PERCENTAGE"							# Type of threshold, “PERCENTAGE” or “ABSOLUTE”
recipients = ['john@corp.com', 'jenny@corp.com']		# The audience that will received the alert when it triggers.
amount = "15"											# Value to assign to the amount property of the budgets
message = "Here your message"							# The message to be sent to the recipients when alert rule is triggered.

###########  -End Config- ###########

# Clear console
print(chr(27) + "[2J")

# Create Tags list.
ownerTags = []

# Setup authentication method 
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

# Create Authentication Dict.
Auth = {}
Auth.update( {'Config' : config} )
Auth.update( {'Signer' : signer} )
Auth.update( {'Use_instance_principal' : use_instance_principal} )
Auth.update( {'Tenancy_id' : tenancy_id} )
Auth.update( {'Top_level_compartment_id' : top_level_compartment_id} ) # Will be empty if you don't filter on a particular compartment


# Create Data Dict.
Data = {}
Data.update( {'Cleanup' : cleanup} )
Data.update( {'OwnerTags' : ownerTags} )
Data.update( {'MyTagNamespace' : myTagNamespace} )
Data.update( {'MyTagKey' : myTagKey} )
Data.update( {'Excluded_tags' : excluded_tags} )
Data.update( {'Threshold_metric' : threshold_metric} )
Data.update( {'Target_type' : "TAG"} )
Data.update( {'Threshold' : threshold} )
Data.update( {'Threshold_type' : threshold_type} )
Data.update( {'Recipients' : recipients} )
Data.update( {'Message' : message} )
Data.update( {'Amount' : amount} )

print("\n===[ Login check ]===")
login(Auth)
if cleanup == "TRUE":
	print(red("cleanup = 'TRUE' => Budgets using not found Tag will be deleted"))

if use_instance_principal == 'TRUE':
    object = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    tenant_name = object.get_namespace().data
    print(yellow(tenant_name))
else:
    object = oci.object_storage.ObjectStorageClient(config=config)
    tenant_name = object.get_namespace().data
    print(yellow(tenant_name))

# Setup Regions
print("\n==={ Target regions: }===")

# get the regions list
HomeRegion = False
all_regions = get_region_subscription_list(Auth, HomeRegion)
target_regions=[]

# Now get the home region
HomeRegion = True
is_home_region = get_region_subscription_list(Auth, HomeRegion)

for region in all_regions:
	if (not target_region_names) or (region.region_name in target_region_names):
		target_regions.append(region)
		print(yellow(region.region_name))

# Setup Compartments
print("\n==={ Retrieving compartments... }===")
if not top_level_compartment_id:
	top_level_compartment_id = tenancy_id
	Auth.update( {'Top_level_compartment_id' : top_level_compartment_id} )  # Now will be fullfilled with tenancy_id

get_compartments = get_compartment_list(Auth)
compartments = []
for compartment in get_compartments:
	if compartment.name not in excluded_compartments:
		compartments.append(compartment)
		#print(compartment.name)
print(yellow("{} compartments will be analyzed".format(len(compartments))))

for region in target_regions:
		
	print (magenta("\n=== [ {} @ {} ] ===".format(region.region_name, profile)))
		
	config["region"] = region.region_name
	region = region.region_name

	 #Create Configuration Dict.
	Conf = {}
	Conf.update( {'Tenant_name' : tenant_name} )
	Conf.update( {'Top_level_compartment_id' : top_level_compartment_id} )
	Conf.update( {'Region' : region} )
	Conf.update( {'Compartments' : compartments} )

	# Call functions to collect tags from different services
	get_bucket_tags(Auth, Conf, Data)
	get_compute_tags(Auth, Conf, Data)	
	get_vcn_tags(Auth, Conf, Data)		

	get_instance_configurations_tags(Auth, Conf, Data)
	get_instance_pools_tags(Auth, Conf, Data)
	get_dedicated_vm_hosts_tags(Auth, Conf, Data)

	get_boot_volumes_tags(Auth, Conf, Data)
	get_boot_volume_backups_tags(Auth, Conf, Data)
	get_block_volumes_tags(Auth, Conf, Data)
	get_block_volume_backups_tags(Auth, Conf, Data)
	get_custom_images_tags(Auth, Conf, Data)

	get_database_tags(Auth, Conf, Data)
	get_autonomous_tags(Auth, Conf, Data)

# Now call the budget function which will use Tags collected previously
manage_budgets(Auth, Conf, Data)
