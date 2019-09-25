# OCI_Resources

Save your credits terminating an instance (Bare Metal or Virtual) when not used.
Relaunch it without losing anything. (e.g: every night / every morning).


The Script keeps EVERY Instance properties:

    - Shape,
    - Compartment,
    - Region,
    - AD,
    - Fault Domain,
    - VCN,
    - Subnet,
    - Private/Public IPs,
    - Boot/Block volumes, 


When the BM Instance is terminated (deleted)
    - the billing is stopped.
    - you only pay for Boot/Block volume storage.


When the instance is recreated
    - it is in the same state,
    - without any differences (like a soft reboot)
    - it also creates backups before terminating an instance


# PRE REQUISITES

    - Create a Control_Instance (e.g: VM.Standard.E2.1.Micro Always Free Eligible) 
    - Install the OCI-CLI on the control_instance 
        https://docs.cloud.oracle.com/iaas/Content/API/SDKDocs/cliinstall.htm
    - Copy the target instance(s) Private_Key on the control_instance
    - Here the Private Key File is named "key"
    - Don't forget to apply proper rights :
        chmod 700 key
    - The target instance must use a reserved Public IP

