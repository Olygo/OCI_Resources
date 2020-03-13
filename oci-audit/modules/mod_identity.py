# coding: utf-8

import oci

yellow = lambda text: '\033[0;33m' + text + '\033[0m'

def login(Auth):

    if Auth["Use_instance_principal"] == 'TRUE':
        identity = oci.identity.IdentityClient(config={}, signer=Auth["Signer"])
        print(yellow("Logged in as Instance Principal: {} ".format(identity)))
    else:
        identity = oci.identity.IdentityClient(config=Auth["Config"])
        user = identity.get_user(Auth["Config"]['user']).data
        print(yellow("Logged in as: {} @ {}".format(user.description, Auth["Config"]['region'])))
