#!/usr/bin/bash
# version: 1.0.0

# PRE REQUISITES
# 
# This script must have access to the .cfg files created by Terminate.sh
# default directory is $HOME/config/
# Instance Must use a reserved PIP
# 


#Set conf directory
dir_conf="$HOME/config"

cd ${dir_conf}

#SET VARIABLES

if [ "$#" -ne 1 ]; then
 echo -e "\033[31mNo private IP argument submited, previous IP will be used\033[0m"
 echo -e "\033[31mTo change private IP use Launch.sh <privateIP>\033[0m"
 echo ""
 privateIp=$(cat privateIp.cfg)
 echo -e "\033[32mPrivate Ip : $privateIp\033[0m"
 else
 privateIp="${1}"
 echo -e "\033[32mPrivate Ip : \033[36m $privateIp\033[0m" 
fi

publicIp=$(cat publicIp.cfg)
echo -e "\033[32m Public Ip: \033[36m $publicIp\033[0m"
compartmentId=$(cat compartmentId.cfg)
echo -e "\033[32m compartmentId: \033[36m $compartmentId\033[0m"
displayName=$(cat displayName.cfg)
echo -e "\033[32m displayName: \033[36m $displayName\033[0m"
shape=$(cat shape.cfg)
echo -e "\033[32m shape: \033[36m $shape\033[0m"
availabilityDomain=$(cat availabilityDomain.cfg)
echo -e "\033[32m availabilityDomain: \033[36m $availabilityDomain\033[0m"
bootVolumeId=$(cat bootVolumeId.cfg)
echo -e "\033[32m bootVolumeId: \033[36m $bootVolumeId\033[0m"
blockVolumeId=$(cat blockVolumeId.cfg)
echo -e "\033[32m blockVolumeId: \033[36m $blockVolumeId\033[0m"
subnetId=$(cat subnetId.cfg)
echo -e "\033[32m subnetId: \033[36m $subnetId\033[0m"
publicIpId=$(cat publicIpId.cfg)
echo -e "\033[32m publicIpId: \033[36m $publicIpId\033[0m"

# Script starts
#########################
#date=$(date +"%d%b%Y_%H-%m")
timeNow=`date +%Y-%m-%d.%H-%M-%S`

echo ""
echo -e "\033[35m*********************\033[0m"
echo -e "\033[35m Script starts...    \033[0m"
echo -e " \033[35m${timeNow}          \033[0m"
echo -e "\033[35m*********************\033[0m"
echo ""

# Create the Instance
# Do not assign a public IP during Instance creation, it will be added just after

echo -e "\033[32mCreating instance...\033[0m"
echo ""
oci compute instance launch --availability-domain ${availabilityDomain} --compartment-id ${compartmentId} --shape ${shape} --assign-public-ip false --display-name ${displayName} --private-ip ${privateIp} --source-boot-volume-id ${bootVolumeId} --subnet-id ${subnetId} --vnic-display-name Vnic_${displayName} --wait-for-state RUNNING  > /dev/null

# Retrieve the new instanceId
echo -e "\033[32mRetrieving new instance Id...\033[0m"
echo ""
oci compute instance list --compartment-id ${compartmentId} --display-name ${displayName} --lifecycle-state RUNNING > metadata_new.cfg
instanceId=$(cat metadata_new.cfg | grep ocid1.instance. | sed 's/"id": "//;s/",//')
echo ${instanceId} > instanceId_new.cfg
echo -e "\033[36m${instanceId}\033[0m"

echo -e "\033[32mRetrieving instance Private Ip Id...\033[0m"
echo ""
oci network private-ip list --ip-address ${privateIp} --subnet-id ${subnetId} > privateIpId_new.cfg
privateIpId=$(cat privateIpId_new.cfg | grep ocid1.privateip. | sed 's/"id": "//;s/",//')
echo ${privateIpId} > privateIpId_new.cfg
echo -e "\033[36m${privateIpId}\033[0m"

echo -e "\033[32mAttaching block volume...\033[0m"
oci compute volume-attachment attach-iscsi-volume --instance-id ${instanceId} --volume-id ${blockVolumeId} --wait-for-state ATTACHED > /dev/null

echo -e "\033[32mAssigning public ip...\033[0m"
oci network public-ip update --force --public-ip-id ${publicIpId} --private-ip-id ${privateIpId} --wait-for-state ASSIGNED  > /dev/null
echo -e "\033[36m${publicIp}\033[0m"
echo ""

echo -e "\033[32mBacking up configuration file to archive_new_$timeNow.tgz\033[0m"
echo
tar -zcvf archive_new_$timeNow.tgz *_new.cfg > /dev/null

#datend=$(date +"%d%b%Y-%H-%m")
timeNow2=`date +%Y-%m-%d.%H-%M-%S`

echo -e "\033[35m********************************\033[0m"
echo -e "\033[32m         Done                   \033[0m"
echo -e "\033[35m Start: \033[32m ${timeNow}              \033[0m"
echo -e "\033[35m Stop:  \033[32m ${timeNow2}             \033[0m"
echo -e "\033[35m Private Ip: \033[32m ${privateIp}       \033[0m"
echo -e "\033[35m Public Ip: \033[32m ${publicIp}         \033[0m"
echo -e "\033[35m********************************\033[0m"
echo
