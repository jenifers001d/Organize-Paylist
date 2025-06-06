# Organize Paylist

This repository contains a simple script to download your payslip
attachments from Gmail and rename them using a date found in the email
body. After downloading, the script marks the processed emails as read.

## Usage

1. Create a Google Cloud project and enable the **Gmail API** with
   permission to modify messages.
2. Download your OAuth client credentials as `credentials.json` and place
   it in the repository directory.
3. Install Python dependencies:

   ```bash
   pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```
4. Run the script:

   ```bash
   python download_payslip.py
   ```

The first run will open a browser window to authorize access to your
Gmail account and will save a `token.json` for subsequent runs.

Adjust the search query or regular expressions in the script to match
your payslip emails.
