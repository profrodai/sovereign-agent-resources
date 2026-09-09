# Integration account tracks for Zeocore 0.10.0

Reviewed 2026-09-09. This catalog uses the released Zeocore setup guides as the
account and credential authority. Its core exercises remain credential-free.
Open the provider guide before copying any example into a live application.

## Choose the track before obtaining credentials

1. Begin with the [release labs](../examples/zeocore-0100/README.md). Their fixture
   transports never reach a provider, regardless of ambient credentials.
2. Read [managed environments](https://github.com/profrodai/zeocore/blob/v0.10.0/docs/integrations/environments.md).
   Create distinct test and production state roots. Select a mode and provider
   explicitly at the application entry point; do not reuse initialized clients
   across modes. Fixture mode is test-only and still requires injected fixtures.
3. For live test E2E, create the separate account/project and credential described
   below. Where the service has no sandbox, a dedicated live test account is the
   test variant. It can still incur charges and send real messages.
4. Verify read-only identity first. Then, if authorized, run one bounded write to
   a disposable resource or opted-in test recipient, inspect the result, and clean
   up only that test's resources. Keep sanitized receipts, not keys.
5. Set up production independently. Confirm account identity, entitlements,
   sender/destination, audience and required host authorization before effects.

## Exact provider instructions

Each linked guide covers how and where to obtain credentials, a test-account
track, a production track, bounded E2E verification, and cleanup/rotation.
These links select the release tag so setup instructions match the installed API.

| Integration | Account/key guide | Local resource |
|---|---|---|
| HubSpot marketing | [Private app, scopes, marketing entitlements and recipient restrictions](https://github.com/profrodai/zeocore/blob/v0.10.0/docs/integrations/hubspot.md) | [Release labs](../examples/zeocore-0100/README.md) |
| Kit marketing | [API v4 key/OAuth, dedicated accounts and sender setup](https://github.com/profrodai/zeocore/blob/v0.10.0/docs/integrations/kit.md) | [Release labs](../examples/zeocore-0100/README.md) |
| Gemini reference images | [AI Studio project/key, billing and host Keychain admission](https://github.com/profrodai/zeocore/blob/v0.10.0/docs/integrations/gemini-images.md) | Request-only release lab |
| Native ZEOconnect | [Pairing, secure session custody and explicit profiles](https://github.com/profrodai/zeocore/blob/v0.10.0/docs/integrations/zeoconnect.md) | Fake service release lab |
| Notion | [Integration token, workspace and page sharing](https://github.com/profrodai/zeocore/blob/v0.10.0/docs/integrations/notion.md) | [Governed upsert](../examples/zeocore-notion-governed-upsert/README.md) |
| Supabase | [Project URL, publishable keys, test projects and RLS](https://github.com/profrodai/zeocore/blob/v0.10.0/docs/integrations/supabase.md) | [Bounded data](../examples/zeocore-supabase-bounded-data/README.md) |
| Google Workspace, GitHub, Bluesky, LLMs and local tools | [Complete setup index](https://github.com/profrodai/zeocore/blob/v0.10.0/docs/integrations/README.md) | [Examples catalog](../examples/README.md) |
| Jupytext, Pandoc and notebook execution | [Authoring reference](https://github.com/profrodai/zeocore/blob/v0.10.0/docs/integrations/authoring-reference.md) | Local authoring release lab |

## Credentials and evidence

Do not paste keys into a notebook, commit `.env`, embed credentials in command
arguments, or post them in an issue. The managed launcher securely prompts for
supported credentials; Gemini requires the host's secret store and authorization
path. Test mode isolates configured state but does not sandbox trusted Python or
remove every credential file visible on the host. Use OS/container isolation if
that is part of your deployment requirement.

A successful simulated send is client evidence, not a delivery receipt. A
successful notebook build is staged material, not a published lesson. Gemini
request construction is neither authorization nor generated output. Preserve
these distinctions when integrating the examples with Sovereign Agent or
ZEO Creator; their runtime must make the relevant admission and approval decisions.
