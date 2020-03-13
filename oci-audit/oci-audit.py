# coding: utf-8

# OCI - Audit
# Written by: Florian Bonneville
# Version 1.0 - march 12 2020

#  This script retrieves action logs about Compute/Database/Autonomous instances 
#  from the audit logs & for a specific compartment.

import datetime
import oci
import os
import configparser
from oci.signer import Signer
from modules.mod_identity import *
from modules.mod_audit import *

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
use_instance_principal = 'FALSE' 	# set 'TRUE' to use instance principal authentication instead of config file
tenancy_id_instance_principal = "ocid1.tenancy.oc1..aaaaaa..."		# specify your tenant OCID 

# --- Script parameters --- #
compartment_ocid = 'ocid1.compartment.oc1..aaaaaaaa....' # specify the OCID of the compartment you want to analyse
start_time = datetime.datetime(2020, 3, 12, 23, 00)
end_time = datetime.datetime(2020, 3, 13, 00, 59)

###########  -End Config- ###########

Events = [
        "CreateAutonomousDatabase",
        "DeleteAutonomousDatabase",
        "StartAutonomousDatabase", 
        "StopAutonomousDatabase",
        "LaunchDbSystem",
        "TerminateDbSystem",
        "LaunchInstance", 
        "InstanceAction",
        "TerminateInstance"
        ]

# Clear console
print(chr(27) + "[2J")

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
Auth.update( {'Compartment_ocid' : compartment_ocid} )
Auth.update( {'Start_time' : start_time} )
Auth.update( {'End_time' : end_time} )

print("\n===[ Login check ]===")
login(Auth)
print()

if use_instance_principal == 'TRUE':
    audit = oci.audit.audit_client.AuditClient(config={}, signer=Auth["Signer"])
else:
    audit = oci.audit.audit_client.AuditClient(config=Auth["Config"])

print("Collecting logs, be patient...")
print()

# Call Function 
get_audit_events(Auth,audit, Events)
