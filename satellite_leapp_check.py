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

LEAPP_VERSION = None
# If a new content view is wanted, put the name of the content view below
# in the "NEW_CV_NAME" variable. Otherwise the content view assigned to
# the host will be used.
#NEW_CV_NAME = ""
HTTP_CHECK = None
USERNAME = None
PASSWORD = None
HOSTNAME = None
SESSION = requests.Session()

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
        USERNAME = input("Enter your Satellite Username")
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

def get_leapp_version():
    global LEAPP_VERSION
    if args.version:
        LEAPP_VERSION = args.version
    else:
        print("RHEL version to leapp to not supplied")
        print("Please use the \"-v\" option to specify a RHEL version to leapp to")
        print("Example: -v 8.6")

def api_call(url, username, password):
    global HTTP_CHECK
    if not HTTP_CHECK:
        try:
            RESPONSE = requests.get("https://"+socket.getfqdn(), timeout=30)
            if RESPONSE.ok:
                HTTP_CHECK = True
        except requests.exceptions.RequestException as error:
            print("A request test to the Satellite at: https://"+
                  str(socket.getfqdn())+" failed with the following error: ")
            print(f"An error occurred: {error}")
    SESSION.auth = (username, password)
    response = SESSION.get(url, verify="/root/ssl-build/katello-server-ca.crt")
    return response

def search_for_host():
    if args.client is not None:
        endpoint = '/api/hosts/'
        try:
            client = api_call(HOSTNAME+endpoint+args.client, USERNAME, PASSWORD)
        except requests.exceptions.RequestException as error:
            print(f"An error occurred: {error}")
        return client.json()
    else:
        print("No client value given")
        print("Please provide a client value with the command")
        print("Example: \"satellite_leapp_check -c client.example.com\"")

def check_org_for_leapp_repos(org_id, leapp_repos):
    endpoint = '/katello/api/organizations/'+org_id+'/repositories'
    repos = api_call(HOSTNAME+endpoint, USERNAME, PASSWORD)
    for repo in repos['results']:
        repo_name = []
        repo_name.append(repo['name'])
    missing_repos = []
    for repo in leapp_repos:
        if repo in repo_name:
            continue
        else:
            missing_repos.append(repo)
    if len(missing_repos) > 0:
        for repo in missing_repos:
            print("Organization ID "+org_id+" is missing "+repo)
        exit
    else:
        return True
    
def check_cv_for_leapp_repos(cv,leapp_repos):
    endpoint = '/katello/api/content_view_versions/'+str(cv)
    cv_info = api_call(HOSTNAME+endpoint, USERNAME, PASSWORD)
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
        for repo in missing_repos:
            print("Content View ID "+cv+" is missing "+repo)
        exit
    else:
        return True
    
def check_repos_for_content(cv_id,leapp_repos,client_lce):
    endpoint = '/katello/api/content_view_versions/'+str(cv_id)
    cv_info = api_call(HOSTNAME+endpoint, USERNAME, PASSWORD)
    repos = cv_info['repositories']
    for repo in repos:
        if repo['name'] in leapp_repos:
            endpoint = '/katello/api/repositories/'+str(repo['id'])
            repo_content = api_call(HOSTNAME+endpoint,USERNAME,PASSWORD)
            empty_repos = []
            if repo_content['content_counts']['rpm'] == 0:
                empty_repos.append(repo['name'])
            else:
                continue
        else:
            continue
    if len(empty_repos) > 0:
        print("The falling repos were found to have 0 RPMs")
        print(empty_repos)
        print("Which means that the repository wasn't synced before the content view was published")
        print("Please sync these repos again and publish a new version of the content view: "+cv_info['content_view']['name'])
        print("Then promote the new version to the client's lifecycle: "+client_lce)
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
        dist_version = client['facts']['distribution::version']
        major = dist_version[0]
        return int(major)
    else:
        print("Client Facts are empty")
        print("Please check if the client is registered and that the client's facts have been updated")
        print("You can update the facts by running the following command on the client:")
        print("    subscription-manager facts --update")

def parse_for_minor_version(client): 
    dist_version = client['facts']['distribution::version']
    minor = dist_version[2]
    return int(minor)

def parse_for_organization(client):
    org_id = client['organization_id']
    return org_id

def parse_client():
    client = search_for_host()
    if parse_for_arch(client) == 'x86_64':
        if parse_for_major_version(client) == 7:
            print("RHEL 7 version detected")
            if parse_for_minor_version < 9:
                print("RHEL version is not the lastest version, please update to version 7.9 before trying to leapp to RHEL 8")
            else:
                org_id = parse_for_organization(client)
                LEAPP_VERSION = get_leapp_version()
                RHEL7_X86_REPOS = ["Red Hat Enterprise Linux 7 Server RPMs x86_64 7Server",
                   "Red Hat Enterprise Linux 7 Server RPMs x86_64 7.9",
                   "Red Hat Enterprise Linux 7 Server - Extras RPMs x86_64",
                   "Red Hat Enterprise Linux 8 for x86_64 - AppStream RPMs "+LEAPP_VERSION,
                   "Red Hat Enterprise Linux 8 for x86_64 - BaseOS RPMs "+LEAPP_VERSION]
                if check_org_for_leapp_repos(org_id,RHEL7_X86_REPOS):
                    print("Organization ID "+org_id+" has the required repos enabled")
                    print("Checking client's content view for repo availability")
                    cv,cv_id = parse_for_content_view(client)
                    if cv != "Default Organization View":
                        if check_cv_for_leapp_repos(cv,RHEL7_X86_REPOS):
                            print("Content View Version ID "+cv+" has the required repositories for leapp upgrade")
                            print("Checking that the repos contain content")
                            client_lce = client['lifecycle_environment_name']
                            if check_repos_for_content(cv_id,RHEL7_X86_REPOS,client_lce):
                                print("Congratulations!!! "+client['name']+' is ready to LEAPP')
                    else:
                        print("You are using the Default Organization View")
                        print("Checking that the repos contain content")
                        client_lce = client['lifecycle_environment_name']
                        if check_repos_for_content(cv_id,RHEL7_X86_REPOS,client_lce):
                            print("Congratulations!!! "+client['name']+' is ready to LEAPP')

        else:
            print("Version detection failed")
        print("Check the client's facts for a 'distribution::version")


def main():
    get_username()
    get_password()
    get_hostname()
    parse_client()


if __name__ == "__main__":
    main()