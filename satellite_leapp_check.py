"""
At the time of this writing the required repos for RHEL7 to RHEL 8 LEAPP 
upgrade to be available in a content view is:
- Red Hat Enterprise Linux 7 Server (RPMs)
    rhel-7-server-rpms
    x86_64 7Server or x86_64 7.9

- Red Hat Enterprise Linux 7 Server - Extras (RPMs)
    rhel-7-server-extras-rpms
    x86_64

- Red Hat Enterprise Linux 8 for x86_64 - AppStream (RPMs)
    rhel-8-for-x86_64-appstream-rpms
    x86_64 8.6

- Red Hat Enterprise Linux 8 for x86_64 - BaseOS (RPMs)
    rhel-8-for-x86_64-baseos-rpms
    x86_64 8.6
"""

import requests
import argparse
import socket
import getpass
import subprocess
import configparser
LEAPP_VERSION = None
RHEL_s390x_REPOS = []
RHEL_ppc64le_REPOS = []
# If a new content view is wanted, put the name of the content view below
# in the "NEW_CV_NAME" variable. Otherwise the content view assigned to
# the host will be used.
#NEW_CV_NAME = ""
HTTP_CHECK = None
USERNAME = None
PASSWORD = None
HOSTNAME = None
SESSION = requests.Session()
SUCCESS = '✅'
FAIL = '❌'
ENABLE_LEAPP_REPOS = {
    "x86_64":{
        "rhel7":[
            "Red Hat Enterprise Linux 7 Server (RPMs)",
            "Red Hat Enterprise Linux 7 Server - Extras (RPMs)"
        ],
        "rhel8":[
            "Red Hat Enterprise Linux 8 for x86_64 - BaseOS (RPMs)",
            "Red Hat Enterprise Linux 8 for x86_64 - AppStream (RPMs)"   
        ]
    },
    "ppc64le":{
        "power8":{
            "rhel7":[
                "Red Hat Enterprise Linux 7 for IBM Power LE (RPMs)",
                "Red Hat Enterprise Linux 7 for IBM Power LE - Extras (RPMs)"
            ],
            "rhel8":[
                "Red Hat Enterprise Linux 8 for Power, little endian - BaseOS (RPMs)",
                "Red Hat Enterprise Linux 8 for Power, little endian - AppStream (RPMs)"
            ]
        },
        "power9":{
            "rhel7":[
                "Red Hat Enterprise Linux 7 for POWER9 (RPMs)",
                "Red Hat Enterprise Linux 7 for POWER9 - Extras (RPMs)"
            ],
            "rhel8":[
                "Red Hat Enterprise Linux 8 for Power, little endian - BaseOS (RPMs)",
                "Red Hat Enterprise Linux 8 for Power, little endian - AppStream (RPMs)"
            ]
        }
    },
    "s390x":{
        "rhel7":[
            "Red Hat Enterprise Linux 7 for System Z (RPMs)",
            "Red Hat Enterprise Linux 7 for System Z - Extras (RPMs)"
        ],
        "rhel8":[
            "Red Hat Enterprise Linux 8 for IBM z Systems - BaseOS (RPMs)",
            "Red Hat Enterprise Linux 8 for IBM z Systems - AppStream (RPMs)"
        ]
    }
}

parser = argparse.ArgumentParser(description="A script to enable, sync, and update content views for clients looking to leapp")
parser.add_argument("-c","--client", action='store', type=str, help="The registered hostname of the RHEL client\n\n\n\n")
parser.add_argument("-v","--version", action='store', type=str, help="The major and minor release you are leapping to. EX: \"8.6\"\n")
parser.add_argument("-u", "--username", action='store', type=str, default=None, help="Satellite WebUI Username\n")
parser.add_argument("-p", "--password", action='store', type=str, default=None, help="Satellite WebUI Password\n")
# parser.add_argument("--newCV", action='store', type=str, default=None,
#                     help="New content view name if user would like to create a new CV"
#                     " instead of updating the current CV assigned to the host")
args = parser.parse_args()

def get_username():
    global USERNAME
    if args.username:
        USERNAME = args.username
    else:
        USERNAME = input("Enter your Satellite Username: ")
    return USERNAME

def get_password():
    global PASSWORD
    if args.password:
        PASSWORD = args.password
    else:
        PASSWORD = getpass.getpass("Enter your Password: ")
    return PASSWORD

def get_hostname():
    global HOSTNAME
    HOSTNAME = 'https://'+str(socket.getfqdn())
    return HOSTNAME

def usage():
    print()
    print("This script is used in determining the availability of the correct repositories for a client for leapp upgrade")
    print("This script currently only supports RHEL 7 to 8 upgrade for x86_64 Intel architecture")

def get_leapp_version():
    if args.version == '8.6' | args.version == '8.8' | args.version == '8.9' | args.version == '8.10':
        LEAPP_VERSION = args.version
    elif args.version == None:
        print(FAIL+" RHEL version to leapp to not supplied")
        print("- Please use the \"-v\" option to specify a RHEL version to leapp to")
        print("- Example:")
        print("  # python satellite_leapp_check.py -c client.example.com -v 8.6 -u admin -p password")
    else:
        print(FAIL+"Leapp version not known")
        print("Leapp version should be either 8.6, 8.8, 8.9, or 8.10")
        print("Please see the following article for supported leapp versions:")
        print("- https://access.redhat.com/articles/4263361")
        print("Your specified version is: "+str(args.version))
        exit(1)
    return LEAPP_VERSION

def determine_leapp_repos(arch):
    # using the arch type, determine what repos are needed
    global LEAPP_VERSION
    LEAPP_VERSION = get_leapp_version()
    RHEL_REPOS = {
        "x86_64":[
            "Red Hat Enterprise Linux 7 Server RPMs x86_64 7Server",
            "Red Hat Enterprise Linux 7 Server RPMs x86_64 7.9",
            "Red Hat Enterprise Linux 7 Server - Extras RPMs x86_64",
            "Red Hat Enterprise Linux 8 for x86_64 - AppStream RPMs "+str(LEAPP_VERSION),
            "Red Hat Enterprise Linux 8 for x86_64 - BaseOS RPMs "+str(LEAPP_VERSION)
                ],
        # need to determine seperation of power 8 and 9
        "ppc64le":[
            "Red Hat Enterprise Linux 7 for IBM Power LE RPMs ppc64le 7.9",
            "Red Hat Enterprise Linux 7 for IBM Power LE RPMs ppc64le 7Server",
            "Red Hat Enterprise Linux 7 for POWER9 - Extras RPMs ppc64le 7Server",
            "Red Hat Enterprise Linux 7 for POWER9 RPMs ppc64le 7Server",
            "Red Hat Enterprise Linux 8 for Power, little endian - BaseOS (RPMs) "+str(LEAPP_VERSION),
            "Red Hat Enterprise Linux 8 for Power, little endian - AppStream (RPMs)"+str(LEAPP_VERSION)
            ],
        # need to determine seperation of system Z and structure A
        "s390x":[
            "Red Hat Enterprise Linux 7 for IBM System z Structure A - Extras RPMs s390x 7Server",
            "Red Hat Enterprise Linux 7 for IBM System z Structure A RPMs s390x 7Server",
            "Red Hat Enterprise Linux 7 for IBM System z Structure A RPMs s390x 7.9",
            "Red Hat Enterprise Linux 7 for System Z - Extras RPMs s390x",
            "Red Hat Enterprise Linux 7 for System Z RPMs s390x 7.9",
            "Red Hat Enterprise Linux 7 for System Z RPMs s390x 7Server",
            "Red Hat Enterprise Linux 8 for IBM z Systems - BaseOS (RPMs)"+str(LEAPP_VERSION),
            "Red Hat Enterprise Linux 8 for IBM z Systems - AppStream (RPMs)"+str(LEAPP_VERSION)
            ]
}
    if arch == 'x86_64':
        return RHEL_REPOS['x86_64']
    elif arch == 's390x':
        return RHEL_REPOS['s390x']
    elif arch == 'ppc64le':
        return RHEL_REPOS['ppc64le']
    else:
        print(FAIL+" Architecture type \""+arch+"\" not supported.")
        print("- Please review the supporte architectures in the documentation:")
        print("  - https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html-single/upgrading_from_rhel_7_to_rhel_8/index#planning-an-upgrade_upgrading-from-rhel-7-to-rhel-8")



def api_call(url, username, password):
    # given the url, username and password make the API call
    global HTTP_CHECK
    if not HTTP_CHECK:
        try:
            RESPONSE = requests.get("https://"+socket.getfqdn(), timeout=30)
            if RESPONSE.ok:
                HTTP_CHECK = True
        except requests.exceptions.RequestException as error:
            print(FAIL+" A request test to the Satellite at: https://"+
                  str(socket.getfqdn())+" failed with the following error: ")
            print(f"An error occurred: {error}")
    SESSION.auth = (username, password)
    response = SESSION.get(url, verify="/root/ssl-build/katello-server-ca.crt")
    return response

def search_for_host():
    # Make the call for the client value on the Satellite
    if args.client:
        endpoint = '/api/hosts/'
        try:
            client = api_call(HOSTNAME+endpoint+args.client, USERNAME, PASSWORD)
        except requests.exceptions.RequestException as error:
            print(f"An error occurred: {error}")
        return client.json()
    else:
        print(FAIL+" No client value given")
        print("- Please provide a client value with the command")
        print("- Example: \"satellite_leapp_check -c client.example.com\"")

def enable_leapp_repos(org_id, arch, releasever,sub_arch=None):
    # Run commands to enable leapp_repos on the Satellite
    command = 'hammer repository-set enable '
    name = '--name '
    release = '--release '
    basearch = '--basearch '
    org = '--organization-id '
    if basearch == "ppc64le":
        if sub_arch:
            for repo in ENABLE_LEAPP_REPOS[basearch][sub_arch]["rhel7"]:
                for version in ['7Server','7.9']:
                    hammer_enable_repo = command+name+repo+' '+release+version+' '+basearch+arch+' '+org+str(org_id)
                    result = subprocess.run(hammer_enable_repo, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if result.returncode == 0:
                        print(SUCCESS+" Repository Enabled: "+repo)
                        print(result.stdout)
                        print("Please sync this repository before attempting to include it in any content view or accessing it via a client") # REMOVE after RFE 2240648
                    else:
                        print(FAIL+" Failed to enable repository: "+repo)
                        print(result.stderr)
                for repo in ENABLE_LEAPP_REPOS[basearch][sub_arch]["rhel8"]:
                    hammer_enable_repo = command+name+repo+' '+release+releasever+' '+basearch+arch+' '+org+str(org_id)
                    result = subprocess.run(hammer_enable_repo, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if result.returncode == 0:
                        print(SUCCESS+" Repository Enabled: "+repo)
                        print(result.stdout)
                        print("Please sync this repository before attempting to include it in any content view or accessing it via a client") # REMOVE after RFE 2240648
                    else:
                        print(FAIL+" Failed to enable repository: "+repo)
                        print(result.stderr)
        else:
            print(FAIL+"Failed to determine if the system was Power8 or Power9, got "+sub_arch+" as returned Power version.")
    else:
        for repo in ENABLE_LEAPP_REPOS[basearch]["rhel7"]:
            for version in ['7Server','7.9']:
                hammer_enable_repo = command+name+repo+' '+release+version+' '+basearch+arch+' '+org+str(org_id)
                result = subprocess.run(hammer_enable_repo, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    print(SUCCESS+" Repository Enabled: "+repo)
                    print(result.stdout)
                    print("Please sync this repository before attempting to include it in any content view or accessing it via a client") # REMOVE after RFE 2240648
                else:
                    print(FAIL+" Failed to enable repository: "+repo)
                    print(result.stderr)
        for repo in ENABLE_LEAPP_REPOS[basearch]["rhel8"]:
            hammer_enable_repo = command+name+repo+' '+release+releasever+' '+basearch+arch+' '+org+str(org_id)
            result = subprocess.run(hammer_enable_repo, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                print(SUCCESS+" Repository Enabled: "+repo)
                print(result.stdout)
                print("Please sync this repository before attempting to include it in any content view or accessing it via a client") # REMOVE after RFE 2240648
            else:
                print(FAIL+" Failed to enable repository: "+repo)
                print(result.stderr)
def sync_leapp_repos(org_id, arch, releasever, leapp_repos):
    # Run commands to sync the leapp repos
    # Not available until RFE 2240648
    pass

def check_org_for_leapp_repos(org_id, leapp_repos):
    endpoint = '/katello/api/organizations/'+str(org_id)+'/repositories'
    repo_call = api_call(HOSTNAME+endpoint, USERNAME, PASSWORD)
    repos = repo_call.json()
    repo_name = []
    for repo in repos['results']:
        repo_name.append(repo['name'])
    missing_repos = []
    for repo in leapp_repos:
        if repo in repo_name:
            continue
        else:
            missing_repos.append(repo)
    if len(missing_repos) > 0:
        for repo in missing_repos:
            print(FAIL+" Organization ID "+str(org_id)+" is missing "+repo)
            return False
    else:
        return True
    
def check_cv_for_leapp_repos(cv,leapp_repos):
    endpoint = '/katello/api/content_view_versions/'+str(cv)
    cv_call = api_call(HOSTNAME+endpoint, USERNAME, PASSWORD)
    cv_info = cv_call.json()
    repos = cv_info['repositories']
    repo_names = []
    missing_repos = []
    for repo in repos:
        repo_names.append(repo['name'])
    for repo in leapp_repos:
        if repo in repo_names:
            continue
        else:
            missing_repos.append(repo)
    if len(missing_repos) > 0:
        print(FAIL+" Content View ("+HOSTNAME+"/content_views/"+str(cv_info['content_view_id'])+"#/versions) is missing the following repositories:")
        for repo in missing_repos:
            print(" - "+repo)
        exit
    else:
        return True
    
def check_repos_for_content(cv_id,leapp_repos,client_lce):
    endpoint = '/katello/api/content_view_versions/'+str(cv_id)
    cv_call = api_call(HOSTNAME+endpoint, USERNAME, PASSWORD)
    cv_info = cv_call.json()
    repos = cv_info['repositories']
    for repo in repos:
        if repo['name'] in leapp_repos:
            endpoint = '/katello/api/repositories/'+str(repo['id'])
            repo_content_call = api_call(HOSTNAME+endpoint,USERNAME,PASSWORD)
            repo_content = repo_content_call.json()
            empty_repos = []
            if repo_content['content_counts']['rpm'] == 0:
                empty_repos.append(repo['name'])
            else:
                continue
        else:
            continue
    if len(empty_repos) > 0:
        print(FAIL+" The following repos were found to have 0 RPMs")
        print("- "+empty_repos)
        print("- Which means that the repository wasn't synced before the content view was published")
        print("- Please sync these repos again and publish a new version of the content view: "+cv_info['content_view']['name'])
        print("- Then promote the new version to the client's lifecycle: "+client_lce)
        exit
    else:
        return True

def parse_for_content_view(client):
    content_view = client['content_facet_attributes']['content_view_name']
    content_view_version_id = client['content_facet_attributes']['content_view_version_id']
    if content_view == "Default Organization View":
        return content_view,content_view_version_id
    else:
        return content_view,content_view_version_id

def parse_for_compliance(client):
    sub_status = client['subscription_status_label']
    if sub_status == 'Simple Content Access':
        return 'SCA'
    if sub_status == "Valid":
        return 'Entitlement'

def parse_for_arch(client):
    arch = client['architecture_name']
    return arch

def parse_for_major_version(client):
    if client['facts']:
        try:
            dist_version = client['facts']['distribution::version']
            major = dist_version[0]
            return int(major)
        except KeyError:
            print(FAIL+" 'distribution::version' fact not present on the system")
    else:
        print(FAIL+" Client Facts are empty")
        print("- Please check if the client is registered and that the client's facts have been updated")
        print("- You can update the facts by running the following command on the client:")
        print("    subscription-manager facts --update")

def parse_for_minor_version(client): 
    dist_version = client['facts']['distribution::version']
    minor = dist_version[2]
    return int(minor)

def parse_for_organization(client):
    org_id = client['organization_id']
    return org_id

def is_satellite(package_name):
    import rpm
    ts = rpm.TransactionSet()
    try:
        mi = ts.dbMatch('name', package_name)
        if mi.count() > 0:
            print(f"{package_name} is installed.")
            return True
        else:
            print(f"{package_name} is not installed.")
            return False
    except rpm.error:
        print("Error: Unable to determine RPM package status.")

'''
Be able to run on the client side to determine if the LEAPP repos are available
we need to check:
- Pull new sub-man certs to ensure all changes to certs are up2date
- view the /etc/pki/entitlement/* certs for RHEL7/8/9 repos
- advise on what to do based on results
'''
def sub_man_refresh():
    try:
        cmd = ['subscription-manager','refresh']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #o, e = proc.communicate()

        if proc.returncode == 0:
            #print(o.decode('UTF-8'))
            return True
        else:
            #print(e.decode('UTF-8'))
            return False
    except requests.exceptions.RequestException as error:
        print(FAIL+"The command 'subscription-manager refresh' returned an error!")
        print(error)
        return False
    
def release_unset():
    cmd = ['subscription-manager','release','--unset']
    subprocess.call(cmd, shell=True)
    
def get_os_major():
    major = open('/etc/redhat-release','r').read().split(' ')[5].split('.')[0]
    return major

def get_release_versions():
    cmd = ['subscription-manager','release','--list']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o,e = proc.communicate()
    return o.decode('UTF-8')

def verify_latest_release_avail(version):
    cmd = ['subscription-manager','release','--set',version]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o,e = proc.communicate()

        if proc.returncode == 0:
            #print(o.decode('UTF-8'))
            return True
        else:
            #print(e.decode('UTF-8'))
            return False
    except requests.exceptions.RequestException as error:
        print(FAIL+"Checking for release version '"+version+"' failed")
        print("The following releases are available for this client's repository set:")
        print(get_release_versions())
        print(e.decode('UTF-8'))
        print(error)
        exit(1)

def enable_repos(major):
    try:
        if major == '7':
            cmd = ['subscription-manager','repos','--enable','rhel-7-server-rpms','--enable','rhel-7-server-extras-rpms']
            subprocess.call(cmd, shell=True)
        elif major == '8':
            cmd = ['subscription-manager','repos','--enable','rhel-8-for-x86_64-appstream-rpms','--enable','rhel-8-for-x86_64-baseos-rpms']
            subprocess.call(cmd, shell=True)
    except requests.exceptions.RequestException as error:
        print(FAIL+"Failed to enable RHEL 7 repositories")
        print(error)

def determine_leapp_version_release_avail(LEAPP_VERSION):
    releasever = get_release_versions()
    LEAPP_VERSION_str = LEAPP_VERSION+'\n'
    if LEAPP_VERSION_str in releasever:
        return True
    else:
        print(FAIL+"Release version '"+LEAPP_VERSION+"' not found in available release versions:")
        print(releasever)
        exit(1)

def repo_file_check(repo_label):
    try:
        config = configparser.ConfigParser()
        config.read('/etc/yum.repos.d/redhat.repo')
        rh_repo_conf = {}
        rh_repo_conf['sslclientcert'] = config[repo_label]['sslclientcert']
        rh_repo_conf['sslclientkey'] = config[repo_label]['sslclientkey']
        rh_repo_conf['sslcacert'] = config[repo_label]['sslcacert']
        rh_repo_conf['serverurl'] = config[repo_label]['baseurl'][:config[repo_label]['baseurl'].find("dist")]
        return rh_repo_conf
    except requests.exceptions.RequestException as error:
        print(FAIL+"Failed to parse file /etc/yum.repos.d/redhat.repo")
        print(error)
        exit(1)

def check_leapp_repos_content(LEAPP_VERSION):
    try:
        if LEAPP_VERSION in ['8.6','8.8','8.9','8.10']:
            rh_repo_conf = repo_file_check('rhel-7-server-rpms')
            for repo in ['appstream','baseos']:
                response = SESSION.get(rh_repo_conf['serverurl']+
                                    'dist/rhel8/'+LEAPP_VERSION+'/x86_64/'+repo+'/os/repodata/repomd.xml',
                                    verify="/root/ssl-build/katello-server-ca.crt",
                                    cert=(rh_repo_conf['sslclientcert'],rh_repo_conf['sslclientkey']))
                if response.status_code != '200':
                    print(FAIL+"Failed to retrieve the repomd.xml from the "+repo+" repository")
                else:
                    return response
    except requests.exceptions.RequestException as error:
        print(error)
        exit(1)

def check_client():
    LEAPP_VERSION = get_leapp_version()
    if sub_man_refresh():
        release_unset()
        major = get_os_major()
        if major == '7':
            verify_latest_release_avail('7Server')
            enable_repos(major)
            determine_leapp_version_release_avail(LEAPP_VERSION)
            check_leapp_repos_content(LEAPP_VERSION)
        elif major == '8':
            verify_latest_release_avail('8')
            enable_repos(major)
            determine_leapp_version_release_avail(LEAPP_VERSION)
            check_leapp_repos_content(LEAPP_VERSION)
        else:
            print(FAIL+"OS major version can not be determined")
            print("OS major release determined from /etc/os-release file")
            print("Found the following as the major release version from this file:")
            print(major)
    else:
        exit(1)
    print(SUCCESS+"Your client is ready to Leapp!")



'''
Check client for the following infractions based on arch
- RHEL major version
- RHEL minor version matches expected latest version
- Check Organization for leapp repos
- Check CV for leapp repos

If Organization doesn't have leapp repos enabled
- enable the required repos
- sync the newly enabled repos
'''
def parse_client():
    client = search_for_host()
    arch = parse_for_arch(client)
    if arch == 'x86_64':
        leapp_repos = determine_leapp_repos(arch)
        if parse_for_major_version(client) == 7:
            print(SUCCESS+" RHEL 7 version detected")
            minor = parse_for_minor_version(client)
            if minor < 9:
                print(FAIL+" RHEL 7.\""+str(minor)+"\" is not the lastest version, please update to version 7.9 before trying to leapp to RHEL 8")
            else:
                org_id = parse_for_organization(client)
                if check_org_for_leapp_repos(org_id,leapp_repos):
                    print(SUCCESS+" Organization ID "+str(org_id)+" has the required repos enabled")
                    print("Checking client's content view for repo availability")
                    cv,cv_id = parse_for_content_view(client)
                    if cv != "Default Organization View":
                        if check_cv_for_leapp_repos(cv_id,leapp_repos):
                            print(SUCCESS+" Content View Version ID "+cv+" has the required repositories for leapp upgrade")
                            print("Checking that the repos contain content")
                            client_lce = client['content_facet_attributes']['lifecycle_environment_name']
                            if check_repos_for_content(cv_id,leapp_repos,client_lce):
                                print(SUCCESS+" Congratulations!!! "+client['name']+' is ready to LEAPP')
                    else:
                        print("You are using the Default Organization View")
                        print("Checking that the repos contain content")
                        client_lce = client['content_facet_attributes']['lifecycle_environment_name']
                        if check_repos_for_content(cv_id,leapp_repos,client_lce):
                            print(SUCCESS+" Congratulations!!! "+client['name']+' is ready to LEAPP')
                else:
                    enable_leapp_repos(org_id, arch, args.version, leapp_repos)
                    if check_org_for_leapp_repos(org_id,leapp_repos):
                        print(SUCCESS+" Organization ID "+str(org_id)+" has the required repos enabled")
                        print("Checking client's content view for repo availability")
                        cv,cv_id = parse_for_content_view(client)
                        if cv != "Default Organization View":
                            if check_cv_for_leapp_repos(cv_id,leapp_repos):
                                print(SUCCESS+" Content View Version ID "+cv+" has the required repositories for leapp upgrade")
                                print("Checking that the repos contain content")
                                client_lce = client['content_facet_attributes']['lifecycle_environment_name']
                                if check_repos_for_content(cv_id,leapp_repos,client_lce):
                                    print(SUCCESS+" Congratulations!!! "+client['name']+' is ready to LEAPP')
                        else:
                            print("You are using the Default Organization View")
                            print("Checking that the repos contain content")
                            client_lce = client['content_facet_attributes']['lifecycle_environment_name']
                            if check_repos_for_content(cv_id,leapp_repos,client_lce):
                                print(SUCCESS+" Congratulations!!! "+client['name']+' is ready to LEAPP')
        else:
            print(FAIL+" Version detection failed")
            print("- Check the client's facts for a 'distribution::version")


def main():
    usage()
    if is_satellite('satellite'):
        get_username()
        get_password()
        get_hostname()
        parse_client()
    else:
        print("No satellite package found, assuming this server is a client")
        get_leapp_version
        check_client()



if __name__ == "__main__":
    main()