# satellite-leapp-check
*Disclaimer: This project or the binary files available in the Releases area are NOT delivered and/or released by Red Hat. This is an independent project to help customers and Red Hat Support team to export and/or collect the data from console.redhat.com for reporting or troubleshooting purposes.*

A script to run on the Satellite or the upgrading client to validate clients have the required repository access for the LEAPP upgrade process.

## SUPPORTED EXECUTION LOCATIONS:
- Satellite or Capsule 6.12+
- RHEL 7 clients of Satellite/Capsule

The purpose of this script is to check against common use case scenarios for content access that happen to block a lot of leapp upgrades from getting started.

**THIS IS NOT A REPLACEMENT FOR THE LEAPP UPGRADE**

The leapp upgrade itself is very indepth and covers a lot of varying issues itself for OS upgrades from RHEL 7 -> 8 or RHEL 8 -> 9. Again, this script doesn't ensure that your leapp upgrade will not experience any issues, but it will test for the most common blockers to getting your leapp upgrade started.


## What is this script testing?
Depending on execution environment (on the leapping host or on a Red Hat Satellite) the following are tested:
### On a Satellite
Validates the following:
- leapp host is registered to the Satellite server
- leapp host's architecture (currently x86_64 is the only supported arch)
- leapp host's major release version (currently RHEL 7 -> 8 is the only supported leapp version check)(RHEL 8 -> 9 coming soon)
- leapp host's minor release verison is the latest version as required by leapp
- Satellite's Organization contains the required leapp repositories (will enable them if missing)
- leapp host's assigned Satellite content view to ensure the required leapp repositories are available
- repositories required contain packages available

### On a leapp client
Validates the following:
- hostname value set in the rhsm.conf is reachable
- no subscription-manager release version is set
- major and minor release version meet the requirement for leapp upgrade
- the minimum required repositories for leapp upgrade are enabled
- the next major version's (version you are leapping to) repositories are reachable (assumes from the same URL as the current RHEL version repositories come from)

### Command options
```
# python3 satellite_leapp_check.py --help
usage: satellite_leapp_check.py [-h] [-c CLIENT] [-v VERSION] [-u USERNAME] [-p PASSWORD]

A script to enable, sync, and update content views for clients looking to leapp

options:
  -h, --help            show this help message and exit
  -c CLIENT, --client CLIENT
                        The registered hostname of the RHEL client
  -v VERSION, --version VERSION
                        The major and minor release you are leapping to. EX: "8.6"
  -u USERNAME, --username USERNAME
                        Satellite WebUI Username
  -p PASSWORD, --password PASSWORD
                        Satellite WebUI Password
```

### Example of running the script from a Satellite server
```
[root@bombsat614 ~]# ./satellite_leapp_check.py -c drone79.usersys.redhat.com

Thanks for using satellite_leapp_check.
Please report all bugs or issues found to https://github.com/taftsanders/satellite-leapp-check/issues
This script is used in determining the availability of the correct repositories for a client for leapp upgrade
This script currently only supports RHEL 7 to 8 upgrade for x86_64 Intel architecture

satellite-installer package detected on executing server
Calling the Satellite API for information on the specified client
Enter your Satellite Username: admin
Enter your Password: 
Searching for host drone79.usersys.redhat.com

Leapp version should be either '8.6', '8.8', '8.9', or '8.10'
        Enter the RHEL version you plan to leapp to: 8.9


✅ RHEL 7 version detected
✅ Organization ID 1 has the required repos enabled
Checking client's content view for repo availability
You are using the Default Organization View
Checking that the repos contain content
✅ Congratulations!!! drone79.usersys.redhat.com is ready to LEAPP
```

### Example of running the script from a Satellite server with unsynced repos
```
[root@bombsat614 ~]# python3 satellite_leapp_check.py -c drone79.usersys.redhat.com

Thanks for using satellite_leapp_check.
Please report all bugs or issues found to https://github.com/taftsanders/satellite-leapp-check/issues
This script is used in determining the availability of the correct repositories for a client for leapp upgrade
This script currently only supports RHEL 7 to 8 upgrade for x86_64 Intel architecture

satellite-installer package detected on executing server
Calling the Satellite API for information on the specified client
Enter your Satellite Username: admin
Enter your Password: 
Searching for host drone79.usersys.redhat.com

Leapp version should be either '8.6', '8.8', '8.9', or '8.10'
        Enter the RHEL version you plan to leapp to: 8.9


✅ RHEL 7 version detected
✅ Organization ID 1 has the required repos enabled
Checking client's content view for repo availability
You are using the Default Organization View
Checking that the repos contain content
❌ The following repos were found to have 0 RPMs
        - Red Hat Enterprise Linux 8 for x86_64 - AppStream RPMs 8.9
        - Red Hat Enterprise Linux 8 for x86_64 - BaseOS RPMs 8.9
Please sync the repositories listed above again.
```

### Example of running the script from a Satellite server with missing repos
```
[root@bombsat614 ~]# python3 satellite_leapp_check.py -c drone79.usersys.redhat.com

Thanks for using satellite_leapp_check.
Please report all bugs or issues found to https://github.com/taftsanders/satellite-leapp-check/issues
This script is used in determining the availability of the correct repositories for a client for leapp upgrade
This script currently only supports RHEL 7 to 8 upgrade for x86_64 Intel architecture

satellite-installer package detected on executing server
Calling the Satellite API for information on the specified client
Enter your Satellite Username: admin
Enter your Password: 
Searching for host drone79.usersys.redhat.com

Leapp version should be either '8.6', '8.8', '8.9', or '8.10'
        Enter the RHEL version you plan to leapp to: 8.9


✅ RHEL 7 version detected
❌ Organization ID 1 is missing Red Hat Enterprise Linux 8 for x86_64 - AppStream RPMs 8.9
✅ Repository Enabled: Red Hat Enterprise Linux 8 for x86_64 - AppStream (RPMs)
Please sync this repository before attempting to include it in any content view or accessing it via a client
✅ Organization ID 1 has the required repos enabled
Checking client's content view for repo availability
You are using the Default Organization View
Checking that the repos contain content
❌ The following repos were found to have 0 RPMs
        - Red Hat Enterprise Linux 8 for x86_64 - AppStream RPMs 8.9
        - Red Hat Enterprise Linux 7 Server - Extras RPMs x86_64
        - Red Hat Enterprise Linux 8 for x86_64 - BaseOS RPMs 8.9
Please sync the repositories listed above again.
```

### Example of running the script non-interactively from a Satellite server
```

```