# Google Sheets Setup

To enable the `SQLite -> Google Sheets` sync (Phase 8), the Hermes Social Agent requires a Google Service Account to authenticate with the Google Sheets API.

Follow these steps to generate the required credentials:

## 1. Create a Project in Google Cloud Console
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., "Hermes Social Agent").

## 2. Enable APIs
1. In your project, go to **APIs & Services** > **Library**.
2. Search for **Google Sheets API** and click **Enable**.
3. Search for **Google Drive API** and click **Enable**.

## 3. Create a Service Account
1. Go to **APIs & Services** > **Credentials**.
2. Click **Create Credentials** > **Service Account**.
3. Give it a name (e.g., `hermes-sheets-sync`) and click **Create and Continue**.
4. Grant it the role of **Editor** (so it can create and edit sheets).
5. Click **Done**.

## 4. Generate JSON Key
1. In the Service Accounts list, click the email address of the account you just created.
2. Go to the **Keys** tab.
3. Click **Add Key** > **Create new key**.
4. Choose **JSON** and click **Create**.
5. A `.json` file will download to your computer.

## 5. Configure Hermes
1. Rename the downloaded file to `google-credentials.json`.
2. Move it to the `config/` directory of this repository: `config/google-credentials.json`.
3. *(Optional)* Ensure your `.env` file points to it if you customize the path. By default, the CLI looks for `config/google-credentials.json`.

## 6. Run the Sync
Once the JSON is in place, you can initialize the workbook and share it with your personal email account so you can view it in your browser:

```bash
python -m hermes_social sync --init --share your.email@gmail.com
```

The CLI will output the URL of the generated Google Sheet. Future syncs can be run simply with:

```bash
python -m hermes_social sync
```
