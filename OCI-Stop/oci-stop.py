# coding: utf-8

import sys
import oci
from oci.signer import Signer
from modules.identity import *
from modules.compute import *
from modules.autonomous_db import *
from modules.db_system import *

########## Configuration ####################
# Specify your config file
configfile = '/home/opc/.oci/config'

# Specify your profile name
profile = 'DEFAULT'

# Set true if using instance principal signing
use_instance_principal = 'FALSE'

# Set top level compartment OCID. Tenancy OCID will be set if null.
top_level_compartment_id = ''

# List compartment names to exclude
excluded_compartments = ['System', 'Sys_Admin']

# if no compartment to exclude, use :
# excluded_compartments = []

# List target regions. All regions will be counted if null.
target_region_names = ['eu-frankfurt-1','eu-zurich-1','uk-london-1']

# if all regions must be checked, use :
#target_region_names = []

# TRUE if you want to use Tags, otherwise FALSE
# Tagged instances you don't want to stop

Use_Tag = 'TRUE'

# In this example if Use_Tag = TRUE
# The script will NOT stop instance using the following values:
# Tag_Namespace : CLOUD-STOP
# Tag_Key : STOP
# Tag Value : FALSE
# Instances running with Value=FALSE will not be stopped
# Instances running without Tags will be stopped


#############################################

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
        print (region.region_name)

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
    print ("\n============[ {} ]================".format(region.region_name))

    config["region"] = region.region_name

    stop_compute_instances(config, signer, target_compartments, Use_Tag)
    stop_database_systems(config, signer, target_compartments, Use_Tag)
    stop_autonomous_dbs(config, signer, target_compartments, Use_Tag)

