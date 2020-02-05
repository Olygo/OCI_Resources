import oci
import csv
import time

black = lambda text: '\033[0;30m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'
yellow = lambda text: '\033[0;33m' + text + '\033[0m'
blue = lambda text: '\033[0;34m' + text + '\033[0m'
magenta = lambda text: '\033[0;35m' + text + '\033[0m'
cyan = lambda text: '\033[0;36m' + text + '\033[0m'
white = lambda text: '\033[0;37m' + text + '\033[0m'

def set_regions(config, signer, use_instance_principal, tenant_name, tenancy_id, region_report, now, errors_log):
    
    if use_instance_principal == 'TRUE':
        object = oci.identity.IdentityClient(config={}, signer=signer)
    else:
        object = oci.identity.IdentityClient(config=config)

             
    err = open(errors_log, mode='a')
    OracleRegions = []
    AllMyRegions = []
    MyNewRegions = []

    print("\n==========================={ Getting all Subscribed Regions }=============================")

    my_regions = oci.pagination.list_call_get_all_results(object.list_region_subscriptions, tenancy_id ).data
    for region in my_regions:
        print(region.region_name)
#        print(region.region_key)        
        AllMyRegions.append(region.region_key) 
    
    print()
    print("Subscribed Region(s): {}".format(len(AllMyRegions)))

    print("\n==========================={ Getting all Oracle Regions }=============================")
    #time to read output
    time.sleep(5)

    OracleExistingRegions = oci.pagination.list_call_get_all_results(object.list_regions).data
    for OracleRegion in OracleExistingRegions:
        print(OracleRegion.name)
#        print(OracleRegion.key)
        OracleRegions.append(OracleRegion.key)

    print()
    print("Available Region(s): {}".format(len(OracleRegions)))

    print("\n==========================={ Looking for new Oracle Region }=============================")

    for OracleNewRegion in OracleRegions:
        CreateRegion = oci.identity.models.CreateRegionSubscriptionDetails(region_key=OracleNewRegion)

        if OracleNewRegion not in AllMyRegions:
            MyNewRegions.append(OracleNewRegion)

            try:
                print(green("Subscribing new Region: " + OracleNewRegion))
                object.create_region_subscription(CreateRegion, tenancy_id)
            except oci.exceptions.ServiceError as e:
                print(red("---------> error. status: {}".format(e)))
                err.write(now)
                err.write("\n")
                err.write("---------> error. status: {}".format(e))
                err.write("\n")
                pass

    if len(MyNewRegions) > 0:
        print(green("Added Region(s): {}".format(len(MyNewRegions))))
        print("waiting {3min} for region activation")
        print()
        time.sleep(180)
    else:
        print("No new region available yet")

    my_new_regions = oci.pagination.list_call_get_all_results(object.list_region_subscriptions, tenancy_id ).data
    for region in my_new_regions:
        with open(region_report, mode='a', newline='') as csvfile:
            fieldnames = ['Profile', 'Region_Name', 'Region_Code', 'Region_Status', 'Is_Home_Region', 'Date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({'Profile': tenant_name, 'Region_Name': region.region_name, 'Region_Code': region.region_key, 'Region_Status': region.status,'Is_Home_Region': region.is_home_region, 'Date': now})

    err.close()