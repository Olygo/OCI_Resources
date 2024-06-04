# coding: utf-8

import sys
import oci
from oci.signer import Signer
from modules.identity import *
from modules.compute import *
from modules.autonomous_db import *
from modules.db_system import *

########## Configuration ####################
# if you want to authenticate through OCI CloudShell, set 'TRUE'
use_cloudshell_auth = 'TRUE'
tenancy_id = "ocid1.tenancy.oc1..aaaaaXXXXXXXXX"

# Specify your config file
configfile = '/home/opc/.oci/config'

# Specify your profile name
profile = 'DEFAULT'

# Set true if using instance principal signing
use_instance_principal = 'FALSE'

# Set top level compartment OCID. Tenancy OCID will be set if null.
top_level_compartment_id = 'ocid1.compartment.oc1.. aaaaaXXXXXXXXX'

# List compartment names to exclude
excluded_compartments = ['ManagedCompartmentForPaaS']

# if no compartment to exclude, use :
# excluded_compartments = []

# List target regions. All regions will be counted if null.
#target_region_names = ['eu-frankfurt-1','eu-zurich-1','uk-london-1']
target_region_names = ['eu-frankfurt-1']

# if all regions must be checked, use :
#target_region_names = []

# TRUE if you want to use Tags, otherwise FALSE
# Tagged instances you don't want to stop

use_tag = 'TRUE'

tag_namespace = 'CLOUD-STOP'
tag_key = 'STOP'
tag_value = 'FALSE'


# In this example if use_tag = TRUE
# The script will NOT stop instance using the following values:
# tag_namespace : CLOUD-STOP
# Tag_Key : STOP
# Tag Value : FALSE
# Instances running with Value=FALSE will not be stopped
# Instances running without Tags will be stopped


#############################################

if use_instance_principal == 'TRUE':
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()

if use_cloudshell_auth == 'TRUE':
    config = {}
    delegation_token = open('/etc/oci/delegation_token', 'r').read()
    signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)
    identity = oci.identity.IdentityClient(config={}, signer=signer)
    print("Logged in as: { CloudShell Auth }")

else:
    # Default config file and profile
    config = oci.config.from_file(configfile, profile)
    tenancy_id = config['tenancy']
    signer = Signer(
        tenancy = config['tenancy'],
        user = config['user'],
        fingerprint = config['fingerprint'],
        private_key_file_location = config['key_file'],
        pass_phrase = config['pass_phrase']
    )


print ("\n===========================[ Login check ]=============================")
login(config, signer,use_cloudshell_auth)

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

    stop_compute_instances(config, signer, target_compartments, use_tag, tag_value, tag_key, tag_namespace)
    stop_database_systems(config, signer, target_compartments, use_tag, tag_value, tag_key, tag_namespace)
    stop_autonomous_dbs(config, signer, target_compartments, use_tag, tag_value, tag_key, tag_namespace)

