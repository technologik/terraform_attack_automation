import argparse
#import subprocess
from terrasnek.api import TFC
import terrasnek.exceptions
import json

# I'm trying to do all with the API
# def check_terraform_binary():
#     try:
#         output = subprocess.check_output("terraform --version".split())
#         output = output.decode('ascii')
#         print("Found %s" % output.split('\n')[0])
#         return True
#     except FileNotFoundError as f:
#         return False

def get_atlas_token():
    # ToDo: implement. Open the default file `~/.terraform.d/credentials.tfrc.json` (support windows/nix?) and get the token for the hostname
    return ""

# do some check to see if we have permissions to do what we need
def check_token_and_permissions(hostname, organization, workspace, token):
    api = TFC(token, url=hostname, verify=False)
    try:
        org_info = api.orgs.show(organization)
    except terrasnek.exceptions.TFCHTTPNotFound:
        print(f"[!] Atlas token doesn't have access to the organization {organization}") 
        return False
    api.set_org(organization)
    try:
        workspace_info = api.workspaces.show(workspace)
        # ToDo: check if the workspace is locked
        print(f"[+] Permissions for the workspace {workspace}")
        print(json.dumps(workspace_info['data']['attributes']['permissions'], indent=4))
        if not workspace_info['data']['attributes']['permissions']['can-queue-run']:
            print("[!] The token doesn't have permissions to queue a run!")
            return False
    except terrasnek.exceptions.TFCHTTPNotFound:
        print(f"[!] Atlas token doesn't have access to the workspace {workspace}") 
        return False
    return True

def get_all_envs(hostname, organization, workspace, token):
    # First we need to create a configuration version with the template
    # https://www.terraform.io/docs/cloud/api/configuration-versions.html#create-a-configuration-version
    # Then upload it: 
    # https://www.terraform.io/docs/cloud/api/configuration-versions.html#upload-configuration-files
    # We could use this example:
    # https://github.com/dahlke/terrasnek/blob/master/test/config_versions_test.py#L76
    # Then we create a run for that configuration version
    # https://www.terraform.io/docs/cloud/api/run.html#sample-payload
    # We would need a loop checking for the run status:
    # https://www.terraform.io/docs/cloud/api/run.html#get-run-details
    # Finally we can get the result of the run with the env vars

def parse_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--hostname', type=str, help="Terraform Cloud or Enterprise URL. eg: https//app.terraform.io", required=True)
    arg_parser.add_argument('--organization', type=str, help="Terraform organization", required=True)
    arg_parser.add_argument('--workspace', type=str, help="Terraform workspace", required=True)
    arg_parser.add_argument('--token', type=str, help="ATLAS token, if not specified the one in the system (~/.terraform.d/credentials.tfrc.json) will be used. To get one run `terraform login HOSTNAME`", required=True)
    # Show all of these under a attacks category
    # ToDo: check that we are at least using one of this
    arg_parser.add_argument('--get_envs', type=str, help="It gets the state file just doing a plan, useful when the ATLAS TOKEN doesn't have permissions to access the state file")
    arg_parser.add_argument('--get_state_file', type=str, help="It gets the state file just doing a plan, useful when the ATLAS TOKEN doesn't have permissions to access the state file")
    arg_parser.add_argument('--get_all_state_files_from_org', type=str, help="Gets the ATLAS TOKEN used during a speculative run (plan), and abuse the implicit permissions to get the state files of all workspaces in the organization")
    arg_parser.add_argument('--exec_command', type=str, help="Runs a command in the container used to run the speculative plan, useful to access TFC infra and access Cloud metadata if misconfigured")    
    return arg_parser.parse_args()

def main():
    args = parse_args()
    # if not check_terraform_binary():
    #     # ToDo: Ideally we would point out to the user the same version as the use used in the workspace. Not sure how to get this.
    #     print("terraform binary not found in your system. You can download from here: https://www.terraform.io/downloads.html")
    #     exit(-1)
    if not args.token:
        # ToDo: get token from default config path
        args.token = get_atlas_token()
    if not check_token_and_permissions(args.hostname, args.organization, args.workspace, args.token):
        exit(-1)
    # ToDo: Based on the attack selected call a different function
    get_all_envs(args.hostname, args.organization, args.workspace, args.token)

if __name__ == "__main__":
    main()