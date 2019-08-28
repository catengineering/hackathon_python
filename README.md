# Azure Dev / Test Environment Hackathon

In this hackathon, you will create a development and testing environment in Azure using the [Python SDK for Azure](https://github.com/Azure/azure-sdk-for-python). The test harness for the scenario is defined in `main.py` and the `./tests/` directory of this repository. These files may not be changed during the hackathon.

At the conclusion of the hackathon, one person from the group will demo the scenario running end-to-end.

## Scenario Overview
The following scenario requirements should be implemented in the `vendor.py` file:
1. Create the dev/test environment
2. Create several Linux Virtual Machines and return a ssh client for the created VMs. See [./tests/test_compute.py](./tests/test_compute.py) for details.
3.  Create an object storage instance and perform basic CRUD operations. See [./tests/test_object_storage.py](./tests/test_object_storage.py)
4.  Create a block storage instance, attach it to the created VM, write a file via sftp, detach the disk, and re-attach to another VM. See [./tests/test_block_storage.py](./tests/test_block_storage.py)
5.  Create a relational database and perform basic CRUD operations. See [./tests/test_relational.py](./tests/relational.py)
6.  Delete the dev/test environment.


## Getting Started 
### Using the development environment
### Authenticate
The scenario will use an [Azure Service Principal](https://docs.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals) to interact with Azure. A service principal has been created for you to use. 

The [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest) is needed to download the credentials. The CLI is already installed in the pre-provisioned 

1. Authenticate with the Azure subscription using your provided username and password:
   
   `
   az login
   `
2. Download the service principal credentials

    `
    az keyvault secret download --vault-name Scenario81Vault -n gov-sp-credentials --file ~/sdk_credentials.json
    `

    `
    export AZURE_AUTH_LOCATION=~/sdk_credentials.json
    `
### Initializing the environment
Basic steps:
1. Initialize the virtual environment
   
   `
   source .venv/bin/activate
    `
2. Run the test harness:
   
   `
   python3 main.py
   `
