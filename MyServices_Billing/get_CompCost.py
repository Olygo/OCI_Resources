# get_CompCost.py
# 
# Get Oracle cloud usage costs per compartments for given date range
# Parameters (picked up from config file)
# Parameters (picked up from compartments file)
#   start_date (format 2018-03-03T23:00:00.000)
#   end_date
#
import requests
import sys
from datetime import datetime, timedelta
import configparser
import os

##########################
# Start Config Section
##########################

configfile = './config.ini'
compartmentfile = './compartments.ini'
mycurrency = '£'

##########################
# Get costs function
##########################

def get_account_charges(username, password, domain, idcs_guid, start_time, end_time):

		# print('User:Pass      = {}/{}'.format(username, "*" * len(password)))
		# print('Domain, IDCSID = {} {}'.format(domain, idcs_guid))
		print()
		print()
		print(tenant.upper())
		print()
		print('Start/End Time = {} to {}'.format(start_time, end_time))
		print()

		# Oracle API needs the milliseconds explicitly
			# for url parameters details check "Retrieve Total Tagged Usage Cost"
			# in https://docs.oracle.com/en/cloud/get-started/subscriptions-cloud/meter/op-api-v1-usagecost-accountid-tagged-get.html 

		url_params = {
			'startTime': start_time.isoformat() + '.000',
			'endTime': end_time.isoformat() + '.000',
			'tags': tagkey,
			'usageType': 'TOTAL',
			'rollupLevel':' RESOURCE',
			'computeTypeEnabled': 'Y'
		}
		# print(url_params)

		resp = requests.get(
			'https://itra.oraclecloud.com/metering/api/v1/usagecost/' +domain + '/tagged',
			# should be similar to :
			#'https://itra.oraclecloud.com/metering/api/v1/usagecost/cacct-k675thnb6gh7b73z8y56r99gmp7r617/tagged',

			auth=(username, password),
			headers={'X-ID-TENANT-NAME': idcs_guid},
			params=url_params
		)
		if resp.status_code != 200:
			# This means something went wrong.
			print('Error in GET: {}'.format(resp.status_code), file=sys.stderr)
			raise Exception

		# Add the cost of all items returned
		total_cost = 0

		print('{:56s} {:>5s} {:>7s} {:3s} {:6s}'.format(
				'ResourceName',
				'Qty',
				'Total',
				'Cur',
				'OvrFlg'))

		for item in resp.json()['items']:

			#Each service could have multiple costs (e.g. in overage)
			for cost in item['costs']:

					print('{:56s} {:5.0f} {:7.2f} {:3s} {:>6s}'.format(
						item['resourceName'],
						cost['computedQuantity'],
						cost['computedAmount'], 
						item['currency'],
						cost['overagesFlag'],))

					total_cost += cost['computedAmount']
		return total_cost

##########################
# Main function
##########################

if __name__ == "__main__":

		# In case we use the tilde (~) home directory character
		configfile = os.path.expanduser(configfile)

		if not os.path.isfile(compartmentfile):
			print('Error: Compartments file not found ({})'.format(compartmentfile), file=sys.stderr)
			sys.exit(0)

		with open(compartmentfile) as file:
			for tagkey in file:
				tagkey = tagkey.strip()    # remove the line Feed <<< \n >>> character at the end of each line 

				# Get date range from command line
				if len(sys.argv) != 3:
					print('Usage: ' + sys.argv[0] + ' <start_date> <end_date>')
					print('       Where date format = dd-mm-yyyy')
					sys.exit()
				else:
					start_date = sys.argv[1]
					end_date = sys.argv[2]

				# In case we use the tilde (~) home directory character
				configfile = os.path.expanduser(configfile)

				if not os.path.isfile(configfile):
					print('Error: Config file not found ({})'.format(configfile), file=sys.stderr)
					sys.exit(0)

				config = configparser.ConfigParser()
				config.read(configfile)

				for tenant in config.sections():

					ini_data = config[tenant]

					# Show usage details
					# Set time component of end date to 23:59:59 to match the behaviour of the Oracle my-services dashboard
					usage = get_account_charges(
					ini_data['username'], ini_data['password'],
					ini_data['domain'], ini_data['idcs_guid'],
					datetime.strptime(start_date, '%d-%m-%Y'),
					datetime.strptime(end_date, '%d-%m-%Y') + timedelta(days=1, seconds=-0.001))

					# Output cost per compartment
					print()
					print('{} {} {:6.2f} {}'.format(tagkey.replace('ORCL:OCICompartmentName=', ''), ': ', usage, mycurrency))
					print()