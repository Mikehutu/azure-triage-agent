# Official sources

Documentation grounding for design decisions. External claims cite these.

| Topic | URL | Used for |
|---|---|---|
| Azure built-in roles — AI + machine learning (Cognitive Services OpenAI User `5e0bd9bd-…61bd`) | https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/ai-machine-learning | `infra/main.bicep` RBAC role GUID |
| Azure AI Search RBAC (Search Index Data Reader `1407120a-…71c8f`) | https://learn.microsoft.com/en-us/azure/search/search-security-rbac | `infra/main.bicep` RBAC role GUID |
| Azure OpenAI Structured Outputs (json_schema, strict) | https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/structured-outputs | `_strict_schema()` (no $ref/$defs, additionalProperties:false) |
| Azure OpenAI client SDK (`AzureOpenAI`, `azure_ad_token_provider`) | https://learn.microsoft.com/en-us/python/api/overview/azure/ai-openai-readme | `src/services/__init__.py` client factories |
| aimock (CopilotKit) — fixtures, MCP/A2A mocks, record & replay | https://aimock.copilotkit.dev | `aimock/` harness; failure-mode fixtures |
| sdd-kit methodology (mock-first, hooks, validator prompt) | https://github.com/Mikehutu/sdd-kit | project process; `docs/mock-first.md` |

Last reviewed: 2026-09-13 (all links verified reachable at time of writing; role GUIDs cross-checked against Microsoft Learn).
