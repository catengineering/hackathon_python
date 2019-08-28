# Azure Dev / Test Environment Hackathon

## Scenario Overview

## Getting Started 
### Setup the development environment
### Authenticate
The scenario will use an [Azure Service Principal (https://docs.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals)] to interact with Azure. A service principal has been created for you to use. 

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

## Core Requirements
Overview of the scenario requirements