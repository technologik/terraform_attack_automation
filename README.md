# terraform_attack_automation
Automation associated with our talk: Attacking and Defending Terraform

This repository contains python scripts to demonstrate the possible attacks to the terraform remote backend.

We have two script to support to different scenarios:
* **TF_attack.py**: When you can directly connect with Terraform Cloud or Enterprise, and you have a valid token to do so.
    
    Example usage:
    ```
    python3 TF_attack.py --hostname app.terraform.io --organization test_org --workspace test_workspace --get_envs
    ```

* **PR_attack.py**: When you don't have direct access, or you don't have a token, but you can do a PR to a github repository linked to TFC/TFE and plans are run automatically.

    Example usage:
    ```
    python3 PR_attack.py
    ```