# Publishing Setup (Phase 11)

The Hermes Social Agent supports automated publishing to LinkedIn, Instagram, and X (Twitter), with a graceful fallback to manual publishing.

## 1. Environment Variables
Update your `.env` file with the platforms you want to enable:

```env
PUBLISHING_DRY_RUN=false

LINKEDIN_ENABLED=true
LINKEDIN_CLIENT_ID=your_id
LINKEDIN_CLIENT_SECRET=your_secret
LINKEDIN_ACCESS_TOKEN=your_token

INSTAGRAM_ENABLED=false
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_ACCOUNT_ID=

X_ENABLED=false
X_API_KEY=
X_API_SECRET=
X_ACCESS_TOKEN=
X_ACCESS_TOKEN_SECRET=
```

## 2. Checking Credentials
To verify that your API credentials are valid before letting the agent publish, run:
```bash
hermes-social publish --check
```

## 3. Dry-Run Mode
If you want to test the full pipeline (including formatting and API payload generation) without actually posting to your social accounts, enable dry-run mode:
```bash
hermes-social publish --dry-run <post_id>
```
You can also set `PUBLISHING_DRY_RUN=true` in `.env` to make this the default behavior for autopilot.

## 4. Manual Fallback
If an API token expires, or if a platform requires a paid API that you haven't enabled, the agent will gracefully fall back to **Manual Publishing**.

It will:
1. Transition the post state to `READY_FOR_MANUAL_PUBLISH`.
2. Generate all the assets and copy.
3. Send a Telegram notification with the assets and text so you can manually copy-paste them to the platform.
