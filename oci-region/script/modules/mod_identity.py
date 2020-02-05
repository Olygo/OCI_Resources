import oci

def login(config, signer, use_instance_principal):
    if use_instance_principal == 'TRUE':
        identity = oci.identity.IdentityClient(config={}, signer=signer)
        print("Logged in as Instance Principal: {} ".format(identity))
    else:
        identity = oci.identity.IdentityClient(config=config)
        user = identity.get_user(config['user']).data
        print("Logged in as: {} @ {}".format(user.description, config['region']))

