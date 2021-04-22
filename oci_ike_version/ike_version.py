# coding: utf-8

# OCI - IKE
# This script will collect all existing IPSEC Tunnels across all compartments & regions to get IKE version (V1/V2)
# Written by: Florian Bonneville
# Version 1.0 - april 22 2021

# How to
# Using CloudShell is recommanded (easier to use)
# therefore, just update your Tenant OCID line 23
# python3 ./ike_version.py

# You can comment/uncomment lines 106 to 118 to customize output.

import oci
from oci.signer import Signer
from modules.identity import *

########## Configuration ####################

# Authenticate through CloudShell (TRUE/FALSE) + tenant OCID
use_cloudshell = 'TRUE'
tenancy_id = 'ocid1.tenancy.oc1..aaaaaaaaXXXXXXXXXXXXXXXXXXXXX'

# Authenticate through config file
configfile = '/home/opc/.oci/config'

# Specify your config file profile name
profile = 'DEFAULT'

# Authenticate through an instance principal (TRUE/FALSE)
use_instance_principal = 'FALSE'

# List compartment names to exclude
excluded_compartments = ['ManagedCompartmentForPaaS']

# List target regions. All regions will be counted if null.
#target_region_names = ['eu-frankfurt-1']
target_region_names = []

#############################################

# Get Auth method:

if use_instance_principal == 'TRUE':
    auth_mode = 'instance_principal'    
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    config = {}
    
if use_cloudshell == 'TRUE':
    auth_mode = 'cloud_shell'
    delegation_token = open('/etc/oci/delegation_token', 'r').read()

    # create the api request signer
    signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)
    config = {}

else:
    auth_mode = 'config_file'
    config = oci.config.from_file(configfile, profile)
    tenancy_id = config['tenancy']
    signer = Signer(
        tenancy = config['tenancy'],
        user = config['user'],
        fingerprint = config['fingerprint'],
        private_key_file_location = config['key_file'],
        pass_phrase = config['pass_phrase']
    )

# Login to OCI
login(config, signer, auth_mode)
print()
print("--- Login successful---")

# Get target regions
all_regions = get_region_subscription_list(config, signer, tenancy_id)
target_regions=[]
for region in all_regions:
	if (not target_region_names) or (region.region_name in target_region_names):
		target_regions.append(region)

# Get target compartments
get_compartments = get_compartment_list(config, signer, tenancy_id)
compartments = []

# Process function
for compartment in get_compartments:
	if compartment.name not in excluded_compartments:
		compartments.append(compartment)

for region in target_regions:		
	config["region"] = region.region_name
	region = region.region_name
	print()
	print ("*** Region: {} ***".format(region))
	print ()

	for compartment in compartments:
		network = oci.core.VirtualNetworkClient(config=config, signer=signer)
		ipsec = network.list_ip_sec_connections(compartment.id).data

		for item in ipsec: #ipsec is a list
			ip_sec_connection_tunnels = network.list_ip_sec_connection_tunnels(item.id).data

			for item in ip_sec_connection_tunnels:
				print("Compartment: {}".format(compartment.name))
				print("Tunnel Name: {}".format(item.display_name))
				print("Tunnel Ip: {}".format(item.vpn_ip))
				print("Tunnel Version: {}".format(item.ike_version))
				print("Tunnel Routing: {}".format(item.routing))
				print("Tunnel Status: {}".format(item.status))
				#print("Tunnel id: {}".format(item.id))
				print("cpe_ip: {}".format(item.cpe_ip))
				#print("lifecycle_state: {}".format(item.lifecycle_state))
				#print("time_created: {}".format(item.time_created))
				#print("time_status_updated: {}".format(item.time_status_updated))
				#print("bgp_session_info: {}".format(item.bgp_session_info))
				#print("encryption_domain_config: {}".format(item.encryption_domain_config))
				print()
