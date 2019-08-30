# Azure Dev / Test Environment Hackathon

In this hackathon, you will create a development and testing environment in Azure using the [Python SDK for Azure](https://github.com/Azure/azure-sdk-for-python). The test harness for the scenario is defined in `main.py` and the `./tests/` directory of this repository. These files may not be changed during the hackathon.

At the conclusion of the hackathon, one person from the group will demo the scenario running end-to-end.

## Scenario Overview
The following scenario requirements should be implemented in the `vendor.py` file:
1. Create the dev/test environment
2. Create several Linux Virtual Machines and return a ssh client for the created VMs. See [./tests/test_compute.py](./tests/test_compute.py) for details.
3.  Create an object storage instance and perform basic CRUD operations. See [./tests/test_object_storage.py](./tests/test_object_storage.py)
4.  Create a block storage instance, attach it to the created VM, write a file via sftp, detach the disk, and re-attach to another VM. See [./tests/test_block_storage.py](./tests/test_block_storage.py)
5.  Create a relational database and perform basic CRUD operations. See [./tests/test_relational.py](./tests/test_relational.py)
6.  Delete the dev/test environment.


## Environment Setup

The recommended development environment relies on [VS Code Remote](https://code.visualstudio.com/docs/remote/remote-overview) to provide a local editing experience over a development machine in Azure. Each hacker has been assigned an Azure Container Instance that includes all of the tools, code, and configuration needed to complete the scenario.


### Local Setup

Complete the following steps on your local machine:

1. Install [VS Code](https://code.visualstudio.com/download)
2. Install the [Remote Extension for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack)
3. Download the [SSH key](https://aka.ms/hackbox_key) to `Downloads/aci`
4. Press `F1` and choose `Remote-SSH: Open Configuration File...`
5. Add the following to your SSH config

```
Host hackbox
    User root
    HostName <your hackbox name>.westus2.azurecontainer.io
    IdentityFile ~/Downloads/aci
```

6. Press `F1` and choose `Remote-SSH: Connect to Host...` and select `hackbox`
7. Go to `File -> Open Folder` and select `/root/hack/`

From here, you can get started with any of the following tasks:

* Open `.py` files to code the solution
* Press `F5` to start debugging the test harness
* Press `Ctrl+\`` to open a new integrated terminal
    * Run `az` commands
    * Run `python main.py` to run the test harness
