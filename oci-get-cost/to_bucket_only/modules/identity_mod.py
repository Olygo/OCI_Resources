# coding: utf-8

import oci
import os
from oci.signer import Signer

def login(use_instance_principal, use_cloudshell_auth, configfile, profile, tenancy_id):
  
    # check authentication mode
    if use_instance_principal == 'TRUE':
        config = {}
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        identity = oci.identity.IdentityClient(config={}, signer=signer)
        print("Logged in as Instance Principal: {} \n".format(identity))

    if use_cloudshell_auth == 'TRUE':
        config = {}
        delegation_token = open('/etc/oci/delegation_token', 'r').read()
        signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)
        identity = oci.identity.IdentityClient(config={}, signer=signer)
        print("Logged in as: { CloudShell Auth }")

    else:
        configfile = os.path.expanduser(configfile)
        config = oci.config.from_file(configfile, profile)

        signer = Signer(
			tenancy = config['tenancy'],
			user = config['user'],
			fingerprint = config['fingerprint'],
			private_key_file_location = config['key_file'],
			pass_phrase = config['pass_phrase']
			)

        tenancy_id = config['tenancy']
        identity = oci.identity.IdentityClient(config=config)
        user = identity.get_user(config['user']).data
        print("Logged in as: {} from {} \n".format(user.name, config['region']))

    # run code    
    tenancy = identity.get_tenancy(tenancy_id)
    tenant_name = tenancy.data.name

    #return a tuple
    return config, signer, tenant_name, tenancy_id
