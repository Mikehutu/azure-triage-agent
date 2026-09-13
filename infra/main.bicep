targetScope = 'resourceGroup'

metadata description = '''
Azure Container Apps deployment for azure-triage-agent.
Zero plaintext secrets: all cloud auth via user-assigned managed identity + RBAC
(Azure OpenAI User, Search Index Data Reader). Env vars carry names/endpoints only.
'''

@description('Location for all resources')
param location string = resourceGroup().location

@description('Container Apps managed environment name')
param environmentName string = 'triage-env'

@description('Container App name')
param containerAppName string = 'azure-triage-agent'

@description('Container image (registry/repo/image:tag)')
param containerImage string

@description('Azure OpenAI account name (existing resource)')
param openAiAccountName string

@description('Azure AI Search service name (existing resource)')
param searchServiceName string

@description('OpenAI chat deployment name')
param chatDeploymentName string = 'gpt-4o-mini'

// Well-known built-in role definition IDs (least privilege).
var roleOpenAiUser = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
var roleSearchIndexDataReader = '1407120a-92aa-4202-b7e9-c0e197c71c8f'

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${containerAppName}-id'
  location: location
  tags: {
    service: 'azure-triage-agent'
  }
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: environmentName
  location: location
  tags: {
    service: 'azure-triage-agent'
  }
}

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: openAiAccountName
}

resource searchService 'Microsoft.Search/searchServices@2023-11-01' existing = {
  name: searchServiceName
}

resource openAiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(managedIdentity.id, roleOpenAiUser, openAiAccount.id)
  scope: openAiAccount
  properties: {
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleOpenAiUser)
  }
}

resource searchRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(managedIdentity.id, roleSearchIndexDataReader, searchService.id)
  scope: searchService
  properties: {
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleSearchIndexDataReader)
  }
}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  tags: {
    service: 'azure-triage-agent'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
      }
    }
    template: {
      containers: [
        {
          name: 'azure-triage-agent'
          image: containerImage
          env: [
            {
              name: 'AZURE_TRIAGE_AZURE_OPENAI_ENDPOINT'
              value: openAiAccount.properties.endpoint
            }
            {
              name: 'AZURE_TRIAGE_AZURE_OPENAI_CHAT_DEPLOYMENT'
              value: chatDeploymentName
            }
            {
              name: 'AZURE_TRIAGE_AZURE_SEARCH_SERVICE_ENDPOINT'
              value: 'https://${searchServiceName}.search.windows.net'
            }
            {
              name: 'AZURE_TRIAGE_AZURE_SEARCH_INDEX_NAME'
              value: 'kb-runbooks-index'
            }
          ]
          resources: {
            // 2023-05-01 type schema requires an integer core count; fractional
            // CPU (PRD: 0.5) needs the newer schema — see docs/validation note.
            cpu: 1
            memory: '1.0Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
      }
    }
  }
}

output endpoint string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output managedIdentityClientId string = managedIdentity.properties.clientId
