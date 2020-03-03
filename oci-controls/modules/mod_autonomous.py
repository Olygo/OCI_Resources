import oci
import csv

red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

Excluded_States = ['TERMINATED', 'TERMINATING']

def get_autonomous_instances(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log, TagNamespaces, TagKeys):
    err = open(errors_log, mode='a')

    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.database.DatabaseClient(config={}, signer=signer)
    else:
        object = oci.database.DatabaseClient(config=config)
    
    print ("\n==========================={ Getting all Autonomous Instances }=============================")
    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_autonomous_databases, compartment_id=compartment.id).data
        for item in items:
            if (item.lifecycle_state not in Excluded_States):
                AllItems.append(item)
                for TagNamespace in TagNamespaces:
                    if TagNamespace in item.defined_tags:
                        for TagKey in TagKeys:
                            if TagKey in item.defined_tags:
                                print ("Owner Tag OK for: {}".format(item.display_name))
                            else:
                                print ("Owner Tag Missing for: {}".format(item.display_name))
                                try:
                                    if cleanup == "YES":
                                        print("Deleting: {}".format(item.display_name))
                                        object.delete_autonomous_database(autonomous_database_id=item.id)
                                    else:
                                        print("Logging in report: {}".format(item.display_name))
                                except oci.exceptions.ServiceError as e:
                                    print("error deleting Autonomous: {}".format(item.display_name))
                                    print("---------> error. status: {}".format(e))
                                    err.write(now) 
                                    err.write("\n")
                                    err.write("---------> error. status: {}".format(e))
                                    err.write("\n")
                                    pass
                                finally:
                                    with open(tags_report, mode='a', newline='') as csvfile:
                                        fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                        writer.writerow({'Profile': tenant_name, 'Service_Type': 'Autonomous_Instances', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
    err.close()

def get_no_byol_autonomous_licences(config, signer, use_instance_principal, tenant_name, region, compartments, licenses_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.database.DatabaseClient(config={}, signer=signer)
    else:
        object = oci.database.DatabaseClient(config=config)
    
    print ("\n==========================={ Checking all Autonomous Instances Licenses }=============================")

    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_autonomous_databases, compartment_id=compartment.id).data
        license_detail = oci.database.models.UpdateAutonomousDatabaseDetails(license_model = 'BRING_YOUR_OWN_LICENSE')
        for item in items:
            tag = item.defined_tags
            try:
                if 'System_Tags' in tag:
                    #print(tag['System_Tags']['Owner'])
                    Owner = tag['System_Tags']['Owner'].rsplit('/', 1)[-1]
                    print("System Owner is " + Owner)

                elif 'Mandatory_Tags' in tag:
                    #print(tag['Mandatory_Tags']['Owner'])
                    Owner = tag['Mandatory_Tags']['Owner'].rsplit('/', 1)[-1]
                    print("Mandatory Owner is " + Owner)
            except oci.exceptions.ServiceError as e:
                print("error getting Owner Tag for: {}".format(item.display_name))
                print("---------> error. status: {}".format(e))
                err.write(now) 
                err.write("\n")
                err.write("---------> error. status: {}".format(e))
                err.write("\n")                
                pass
            if (item.is_free_tier == False ):           # Exclude Free Tier which are always 'LICENSE_INCLUDED')
                if (item.lifecycle_state not in Excluded_States): #test si l'état de la DB fait partie de ma liste Excluded_States
                    if (item.license_model != 'LICENSE_INCLUDED'):
                        print(green("    * {} ({}) in {}".format(item.display_name, item.license_model, compartment.name)))
                    else:
                        print(red("    * {} ({}) in {}".format(item.display_name, item.license_model, compartment.name)))
                        AllItems.append(item)
                        try:
                            print("Updating License for: {}".format(item.display_name))
                            object.update_autonomous_database(item.id,license_detail)
                        except oci.exceptions.ServiceError as e:
                            print("error updating license for: {}".format(item.display_name))
                            print("---------> error. status: {}".format(e))
                            err.write(now) 
                            err.write("\n")
                            err.write("---------> error. status: {}".format(e))
                            err.write("\n")
                            pass
                        finally:
                            with open(licenses_report, mode='a', newline='') as csvfile:
                                fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'License_Type', 'Compartment', 'Region', 'Owner']
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                writer.writerow({'Profile': tenant_name, 'Service_Type': 'Autonomous_Instances', 'Service_Name': item.display_name, 'License_Type': item.license_model, 'Compartment': compartment.name, 'Region': region, 'Owner': Owner})
    err.close()
