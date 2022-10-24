# coding: utf-8

import oci, os
from os import system, name

yellow = lambda text: '\033[0;33m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

def clear():

	# for windows
	if name == 'nt':
		_ = system('cls')

	# for mac and linux(here, os.name is 'posix')
	else:
		_ = system('clear')

def get_tenancy(tenancy_id, config, signer):
    identity = oci.identity.IdentityClient(config, signer=signer)
    tenancy = identity.get_tenancy(tenancy_id)

    return tenancy.data.name

##########################################################################
# Create signer for Authentication
# Input - config_file, config_profile and is_instance_principals and is_delegation_token
# Output - config and signer objects
##########################################################################

def create_signer(auth_mode, config_file, config_profile):

    # if instance principals authentication
    if str.upper(auth_mode) == 'IP':
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            config = {'region': signer.region, 'tenancy': signer.tenancy_id}
            print(green(f"Successfuly authenticated through Instance Principal: {signer}"))
            return config, signer

        except Exception:
            print(red("Error obtaining instance principal certificate, aborting"))
            raise SystemExit

    # if Delegation Token authentication
    elif str.upper(auth_mode) == 'CS':

        try:
            # check if env variables OCI_CONFIG_FILE, OCI_CONFIG_PROFILE exist and use it
            env_config_file = os.environ.get('OCI_CONFIG_FILE')
            env_config_section = os.environ.get('OCI_CONFIG_PROFILE')

            # check if file exist
            if env_config_file is None or env_config_section is None:
                print(red("This is not a Cloud Shell instance, abort..."))
                raise SystemExit

            config = oci.config.from_file(env_config_file, env_config_section)
            delegation_token_location = config["delegation_token_file"]

            with open(delegation_token_location, 'r') as delegation_token_file:
                delegation_token = delegation_token_file.read().strip()
                # get signer from delegation token
                signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)
                print(green(f"Successfuly authenticated through Cloud Shell: {signer}"))
                return config, signer
    
        except KeyError:
            print(red("This is not a Cloud Shell instance, abort..."))
            raise SystemExit

        except Exception:
            raise

    # config file authentication
    else:
        try:
            config = oci.config.from_file(
                (config_file if config_file else oci.config.DEFAULT_LOCATION),
                (config_profile if config_profile else oci.config.DEFAULT_PROFILE)
            )
            signer = oci.signer.Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=oci.config.get_config_value_or_default(config, "pass_phrase"),
                private_key_content=config.get("key_content")
            )
            print(green(f"Successfuly authenticated through Config File: {config_file}, Config Profile: {config_profile}"))

        except:
            print(red("OCI Config File not found, abort... "))
            raise SystemExit

        return config, signer

def print_conf (auth_mode,config_file,config_profile,month,year,use_history,start_after,prefix_file,working_folder,dest,target_comp,target_bucket,init_reports,tag_reports,tree_reports):
  print()
  print(yellow(f"  -auth_mode: {auth_mode}"))
  print(yellow(f"  -config_file: {config_file}"))
  print(yellow(f"  -config_profile: {config_profile}"))
  print(yellow(f"  -month: {month}"))
  print(yellow(f"  -year: {year}"))
  print(yellow(f"  -use_history: {use_history}"))
  print(yellow(f"  -start_after: {start_after}"))
  print(yellow(f"  -prefix_file: {prefix_file}"))
  print(yellow(f"  -working_folder: {working_folder}"))
  print(yellow(f"  -dest: {dest}"))
  print(yellow(f"  -target_comp: {target_comp}"))
  print(yellow(f"  -target_bucket: {target_bucket}"))
  print(yellow(f"  -init_reports: {init_reports}"))
  print(yellow(f"  -tag_reports: {tag_reports}"))
  print(yellow(f"  -tree_reports: {tree_reports}"))
