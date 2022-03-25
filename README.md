# terraform_attack_automation
Automation associated with our talk: Attacking and Defending Terraform

This repository contains python scripts to demonstrate the possible attacks to the terraform remote backend.

We have two script to support two different scenarios:
* **TF_attack.py**: When you can directly connect with Terraform Cloud or Enterprise, and you have a valid token to do so.
    
    Example usage:
    ```
    python3 TF_attack.py --hostname app.terraform.io --organization test_org --workspace test_workspace --get_envs
    ```

    Example using apply on plan:
    ```
    python3 TF_attack.py --hostname app.terraform.io --organization test_org --workspace test_workspace --apply_on_plan --aws_access_key_variable aws_access_key --aws_secret_key_variable aws_secret_key
    ```

* **PR_attack.py**: When you don't have direct access, or you don't have a token, but you can do a PR to a github repository linked to TFC/TFE and plans are run automatically.

    Example usage:
    ```
    python3 PR_attack.py --repo https://github.com/user/repo/folder/ --get_envs
    ```