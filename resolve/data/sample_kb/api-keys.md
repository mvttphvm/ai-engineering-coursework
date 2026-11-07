# Creating and managing API keys

API keys authenticate your applications with the Resolve API. Treat a key like
a password: anyone who has it can act as your account through the API.

## Create an API key

1. Go to **Settings → Developers → API keys** (you must be an account admin).
2. Click **Create key**, give it a descriptive name, and choose its scopes.
3. Click **Create**. The full key is shown exactly once — copy it into your
   password manager or secrets store immediately. We store only a hashed
   version and can never show it again.

Keys start with `rsv_live_` for production or `rsv_test_` for the sandbox
environment. Test keys can only access sandbox data and never incur charges.

## Scopes and least privilege

Choose only the scopes your application needs: `read:documents`,
`write:documents`, `read:tickets`, `write:tickets`, or `admin:billing`
(admins only). A key cannot exceed the permissions of the user who created it,
and keys created by a user stop working if that user is removed from the
account.

## Rotate and revoke keys

We recommend rotating production keys every 90 days. To rotate without
downtime: create a new key, update your application's configuration, verify the
new key works, then revoke the old key. Revoking a key takes effect immediately
and cannot be undone — requests made with a revoked key return a
`401 invalid_api_key` error.

## If a key is leaked

Revoke the key immediately under **Settings → Developers → API keys**, then
create a replacement. Check **Settings → Developers → API activity** for
requests you do not recognize. If you see API activity you cannot explain,
contact support and we will review the account for compromise.

## Rate limits

API keys are limited to 600 requests per minute per key. When you exceed the
limit, the API returns `429 Too Many Requests` with a `Retry-After` header.
Usage by key is visible under **Settings → Developers → Usage**.
