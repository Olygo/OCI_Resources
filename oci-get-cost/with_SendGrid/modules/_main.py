# coding: utf-8

from modules.compartment_mod import manage_compartment
from modules.bucket_mod import manage_bucket, updload_file
from modules.usage_mod import get_usage, get_usage_details

def _main(config, signer, my_tenant, tenancy_id, my_compartment, my_bucket, start_date, end_date):

	# call compartment function
	my_compartment_id = manage_compartment(config, signer, tenancy_id, my_compartment)

	# call bucket function
	manage_bucket(config, signer, my_compartment_id, my_bucket, tenancy_id)

	# set gathering period
	print("\nGathering OCI billing data for tenant [ {} ] ... \n".format(my_tenant))

	start_at = start_date + "T00:00:00.000Z"
	end_at = end_date + "T00:00:00.000Z"

	# call usage function for the period
	usages = get_usage(config, signer, tenancy_id, end_at, start_at)

	# call usage details function
	monthly_data = get_usage_details(config, signer, my_tenant, tenancy_id, usages, start_date, end_date)

	# print headers
	headers = '{:18s} {:12s} {:12s} {:7s} {:3s}'.format(
		'Tenant',
		'Usage start',
		'Usage end',
		'Amount',
		'Currency')
	print(headers)

	# init local file
	local_file = "oci_consumption_{}_{}.txt".format(my_tenant,end_date)
	f = open(local_file, "a")
	f.write(headers)
	f.write("\n")

	# print consumption for each month
	for i in monthly_data:
		print(monthly_data[i])
		# write to local file
		f.write("{:30s}".format(monthly_data[i]))
		f.write("\n")
	print()

	# close local file before upload
	f.close()
		
	# upload file to bucket
	updload_file(config, signer, my_bucket, local_file, tenancy_id)

	return local_file