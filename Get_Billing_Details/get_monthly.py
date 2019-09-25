# get_monthly.py
#
# Get Oracle cloud monthly charge
# Parameters (picked up from config file)
#   start_date (format 2018-03-03T23:00:00.000)
#   end_date
#
import requests
import sys
from datetime import datetime, timedelta
import configparser
import os

##########################
# Config Section
##########################

configfile = './config.ini'

##########################
# Get costs function
##########################

def get_account_charges(username, password, domain, idcs_guid, start_time, end_time):

	# Oracle API needs the milliseconds explicitly
	url_params = {
		'startTime': start_time.isoformat() + '.000',
		'endTime': end_time.isoformat() + '.000',
		'usageType': 'TOTAL',
		'computeTypeEnabled': 'Y'
	}

	resp = requests.get(
		'https://itra.oraclecloud.com/metering/api/v1/usagecost/' + domain,
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

	for item in resp.json()['items']:

		# Each service could have multiple costs (e.g. in overage)
		for cost in item['costs']:

			if cost['computeType'] == 'Usage':
				total_cost += cost['computedAmount']

	return total_cost

if __name__ == "__main__":
        # Get profile from command line
        if len(sys.argv) != 3:
            print('Usage: ' + sys.argv[0] + ' <profile_name> <start_date> <end_date>')
            print('       Where date format = dd-mm-yyyy')
            sys.exit()
        else:
        #	profile_name = sys.argv[1]
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

            # Simple output
            print('{:24s} {:6.2f}'.format(tenant, usage))

