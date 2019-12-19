# OCI-STOP


Based on the original code of Masataka Marukawa
	
		https://github.com/mmarukaw

- Stop Compute/Autonomous/DBsys Instances.
- Connect to every profile in Oci Config file
- To every region or not
- To every compartment or not

		In this example if Use_Tag = TRUE
		The script will NOT stop instance using the following values:
			- Tag_Namespace : CLOUD-STOP
			- Tag_Key : STOP
			- Tag Value : FALSE
				- Instances running with Value=FALSE will not be stopped
				- Instances running without Tags will be stopped
