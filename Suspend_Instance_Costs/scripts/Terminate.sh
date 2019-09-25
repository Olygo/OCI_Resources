#!/usr/bin/bash

# Version: 1.0.0
# Usage:
# Terminate.sh <privateIP>
#

# PRE REQUISITES
#
#    - Copy the BM_Server Private_Key locally on the BM_Control Server
#    - Here the Private Key File is named "key"
#    - Don't forget to apply proper rights :
#      chmod 700 key
#

#####################
# Configuration data
####################
bm_ip="${1}"
#bm_ip="10.0.0.2"
bm_user="opc"
bm_key_path="$HOME/key"
dir_conf="$HOME/config"


#########################
# Script starts
#########################

if [ "$#" -ne 1 ]; then
 echo "Please provide argument"
 echo "Terminate.sh <privateIP>"
 exit
fi

#date=$(date +"%d%b%Y-%H-%m")
timeNow=`date +%Y-%m-%d.%H-%M-%S`

echo -e "\033[35m*********************\033[0m"
echo -e "\033[35m    Script starts    \033[0m"
echo -e "\033[35m     ${timeNow}      \033[0m"
echo -e "\033[35m*********************\033[0m"
echo

# Check for dir, if not found create it using mkdir
[ ! -d "${dir_conf}" ] && mkdir -p "${dir_conf}"

# Retrieve BM's Metadata
echo -e "\033[32mRetrieving ${bm_ip} Metadata\033[0m"
echo ""
echo -e "\033[32mConnecting SSH: ${bm_ip}...\033[0m"
echo ""
ssh -i ${bm_key_path} ${bm_user}@${bm_ip} 'curl -L http://169.254.169.254/opc/v1/instance/' > ${dir_conf}/metadata.cfg
cd ${dir_conf}
echo -e "\031[32mExiting SSH: ${bm_ip}...\033[0m"
echo ""

# Export metadata to variables
echo -e "\033[32mExtracting ${bm_ip} Metadata...\033[0m"
availabilityDomain=$(cat metadata.cfg  | grep availabilityDomain | sed 's/"availabilityDomain" : "//;s/",//')
echo -e "\033[32mAvailability Domain: \033[36m${availabilityDomain}\033[0m"
faultDomain=$(cat metadata.cfg | grep faultDomain | sed 's/"faultDomain" : "//;s/",//')
echo -e "\033[32mFault Domain: \033[36m${faultDomain}\033[0m"
compartmentId=$(cat metadata.cfg | grep compartmentId | sed 's/"compartmentId" : "//;s/",//')
echo -e "\033[32mCompartment Id: \033[36m${compartmentId}\033[0m"
displayName=$(cat metadata.cfg | grep displayName | sed 's/"displayName" : "//;s/",//')
echo -e "\033[32mDisplay Name: \033[36m${displayName}\033[0m"
instanceId=$(cat metadata.cfg | grep ocid1.instance. | sed 's/"id" : "//;s/",//')
echo -e "\033[32mInstance Id: \033[36m${instanceId}\033[0m"
imageId=$(cat metadata.cfg | grep image | sed 's/"image" : "//;s/",//')
echo -e "\033[32mImage Id: \033[36m${imageId}\033[0m"
ssh_authorized_keys=$(cat metadata.cfg | grep ssh_authorized_keys | sed 's/"ssh_authorized_keys" : "//;s/"//')
# echo "ssh_authorized_keys: ${ssh_authorized_keys}"
region=$(cat metadata.cfg | grep region | sed 's/"region" : "//;s/",//')
echo -e "\033[32mRegion: \033[36m${region}\033[0m"
shape=$(cat metadata.cfg | grep shape | sed 's/"shape" : "//;s/",//')
echo -e "\033[32mshape: \033[36m${shape}\033[0m"
echo ""

# Record variables to files
echo ${availabilityDomain} > availabilityDomain.cfg
echo ${faultDomain} > faultDomain.cfg
echo ${compartmentId} > compartmentId.cfg
echo ${displayName} > displayName.cfg
echo ${instanceId} > instanceId.cfg
echo ${imageId} > imageId.cfg
echo ${ssh_authorized_keys} > ssh_authorized_keys.cfg
echo ${region} > region.cfg
echo ${shape} > shape.cfg

# Retrieve Boot Volume Disk Id

echo -e "\033[32mRetrieving ${displayName} Boot Volume...\033[0m"
oci compute boot-volume-attachment list --availability-domain ${availabilityDomain} --compartment-id ${compartmentId} --instance-id ${instanceId} > bootVolumeMetadata.cfg
bootVolumeId=$(cat bootVolumeMetadata.cfg | grep boot-volume-id | sed 's/     "boot-volume-id": "//;s/",//')
echo ${bootVolumeId} > bootVolumeId.cfg
echo -e "\033[36m${bootVolumeId}\033[0m"
echo ""

# Retrieve Block Volume Disk Id
echo -e "\033[32mRetrieving ${displayName} Block Volume...\033[0m"
oci compute volume-attachment list --availability-domain ${availabilityDomain} --compartment-id ${compartmentId} --instance-id ${instanceId} > blockVolumeMetadata.cfg
blockVolumeId=$(cat blockVolumeMetadata.cfg | grep volume-id | sed 's/"volume-id": "//;s/"//')
echo ${blockVolumeId} > blockVolumeId.cfg
echo -e "\033[36m${blockVolumeId}\033[0m"
echo ""

# Retrieve Network details
oci compute vnic-attachment list --compartment-id ${compartmentId} --instance-id ${instanceId} > vnicMetadata.cfg
vnicId=$(cat vnicMetadata.cfg | grep vnic-id | sed 's/"vnic-id": "//;s/"//')
echo ${vnicId} > vnicId.cfg

echo -e "\033[32mRetrieving ${displayName} Subnet...\033[0m"
subnetId=$(cat vnicMetadata.cfg | grep subnet-id | sed 's/"subnet-id": "//;s/",//')
echo ${subnetId} > subnetId.cfg
echo -e "\033[36m${subnetId}\033[0m"
echo ""

echo -e "\033[32mRetrieving ${displayName} Public IP...\033[0m"
oci network vnic get --vnic-id ${vnicId} > ip.cfg
publicIp=$(cat ip.cfg | grep public-ip | sed 's/"public-ip": "//;s/",//')
echo ${publicIp} > publicIp.cfg
echo -e "\033[36m${publicIp}\033[0m"
echo ""

echo -e "\033[32mRetrieving ${displayName} Private IP...\033[0m"
privateIp=$(cat ip.cfg | grep private-ip | sed 's/"private-ip": "//;s/",//')
echo ${privateIp} > privateIp.cfg
echo -e "\033[36m${privateIp}\033[0m"
echo ""

oci network private-ip list --subnet-id ${subnetId} --ip-address ${privateIp} > privateIpMetadata.cfg
privateIpId=$(cat privateIpMetadata.cfg | grep ocid1.privateip. | sed 's/"id": "//;s/",//')
echo ${privateIpId} > privateIpId.cfg

oci network public-ip get --private-ip-id ${privateIpId} > publicIpMetadata.cfg
publicIpId=$(cat publicIpMetadata.cfg | grep ocid1.publicip. | sed 's/"id": "//;s/",//')
echo ${publicIpId} > publicIpId.cfg

echo -e "\033[31mStopping instance...\033[0m"
echo "Waiting until the resource has entered state: STOPPED..."
echo ""
oci compute instance action --action SOFTSTOP --instance-id ${instanceId} --wait-for-state STOPPED > /dev/null

echo -e "\033[32mBacking up Boot Volume...\033[0m"
echo "Waiting until the resource has entered state: AVAILABLE..."
echo ""
oci bv boot-volume-backup create --boot-volume-id ${bootVolumeId} --type full --display-name ${displayName}_boot_$timeNow --wait-for-state AVAILABLE > /dev/null

echo -e "\033[32mBacking up Block Volume...\033[0m"
echo "Waiting until the resource has entered state: AVAILABLE..."
echo ""
oci bv backup create --volume-id ${blockVolumeId} --type full --display-name ${displayName}_block_$timeNow --wait-for-state AVAILABLE > /dev/null

echo -e "\033[31mTerminating instance...\033[0m"
echo "Waiting until the resource has entered state: TERMINATED..."
echo ""

oci compute instance terminate --instance-id ${instanceId} --force --preserve-boot-volume true --wait-for-state TERMINATED > /dev/null

echo -e "\033[32mBacking up configuration file to archive_$timeNow.tgz\033[0m"
echo
tar -zcvf archive_$timeNow.tgz *.cfg > /dev/null

timeNow2=`date +%Y-%m-%d.%H-%M-%S`
echo -e "\033[35m*********************\033[0m"
echo -e "\033[35m      Done           \033[0m"
echo -e "\033[35m Start: ${timeNow}   \033[0m"
echo -e "\033[35m Stop:  ${timeNow2}  \033[0m"
echo -e "\033[35m*********************\033[0m"
echo

