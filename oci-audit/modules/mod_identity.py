# coding: utf-8

import oci

yellow = lambda text: '\033[0;33m' + text + '\033[0m'

def login(Auth):

    if Auth["Use_instance_principal"] == 'TRUE':
        identity = oci.identity.IdentityClient(config={}, signer=Auth["Signer"])
        print(yellow("Logged in as Instance Principal: {} ".format(identity)))
    if Auth["Use_cloudshell"] == 'TRUE':
        config = {}
        delegation_token = open('/etc/oci/delegation_token', 'r').read()
        signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)
        identity = oci.identity.IdentityClient(config={}, signer=signer)
        print("Logged in as: { CloudShell Auth }")
        
    else:
        identity = oci.identity.IdentityClient(config=Auth["Config"])
        user = identity.get_user(Auth["Config"]['user']).data
        print(yellow("Logged in as: {} @ {}".format(user.description, Auth["Config"]['region'])))
