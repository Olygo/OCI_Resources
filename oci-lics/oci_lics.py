# coding: utf-8

import sys
import oci
import configparser
from oci.signer import Signer
from modules.identity import *
from modules.adb_mod import *
from modules.dbsys_mod import *
import datetime

black = lambda text: '\033[0;30m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'
yellow = lambda text: '\033[0;33m' + text + '\033[0m'
blue = lambda text: '\033[0;34m' + text + '\033[0m'
magenta = lambda text: '\033[0;35m' + text + '\033[0m'
cyan = lambda text: '\033[0;36m' + text + '\033[0m'
white = lambda text: '\033[0;37m' + text + '\033[0m'

########## Configuration ####################
# Specify your config file
configfile = '/home/opc/.oci/config'

# Set true if using instance principal signing
use_instance_principal = 'TRUE'

# Set top level compartment OCID. Tenancy OCID will be set if null.
#top_level_compartment_id = ''

# List compartment names to exclude
excluded_compartments = ['ManagedCompartmentForPaaS']

# if no compartment to exclude, use :
# excluded_compartments = []

# List target regions. All regions will be counted if null.
#target_region_names = ['eu-frankfurt-1','eu-zurich-1','uk-london-1']

# if all regions must be checked, use :
target_region_names = []

#############################################

now = datetime.datetime.now()
print(now)

config = configparser.ConfigParser()
config.read(configfile)

# For each tenant/profile in the config file
for profile in config.sections():

    # Set top level compartment OCID. Tenancy OCID will be set if null.
	top_level_compartment_id = ''

	print (cyan("\n===========================[ {} ]===========================".format(profile)))

    ###############################################
    
    # Default config file and profile
	config = oci.config.from_file(configfile, profile)
	tenancy_id = config['tenancy']

	if use_instance_principal == 'TRUE':
		signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
	else:
		signer = Signer(
	        tenancy = config['tenancy'],
    	    user = config['user'],
        	fingerprint = config['fingerprint'],
        	private_key_file_location = config['key_file'],
        	pass_phrase = config['pass_phrase']
    		)

	print ("\n===========================[ Login check ]=============================")
	login(config, signer)

	print ("\n==========================[ Target regions ]===========================")
	all_regions = get_region_subscription_list(config, signer, tenancy_id)
	target_regions=[]
	for region in all_regions:
		if (not target_region_names) or (region.region_name in target_region_names):
			target_regions.append(region)

	print ("\n========================[ Target compartments ]========================")
	if not top_level_compartment_id:
		top_level_compartment_id = tenancy_id
	compartments = get_compartment_list(config, signer, top_level_compartment_id)
	target_compartments=[]

	for compartment in compartments:
		if compartment.name not in excluded_compartments:
			target_compartments.append(compartment)
			print (compartment.name)

	for region in target_regions:
		print (magenta("\n============[ {} @ {} ]================".format(region.region_name, profile)))

		config["region"] = region.region_name

		change_autonomous_db_license(config, signer, target_compartments)
		stop_database_systems(config, signer, target_compartments)
