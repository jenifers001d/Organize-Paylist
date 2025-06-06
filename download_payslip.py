"""Download and rename payslip PDFs from Gmail.

This script searches for unread Gmail messages with a subject like
"Payslip for Zhu-Rong Zheng for Week ending" and saves the PDF
attachment as ``PaySlip YYYYMMDD - YYYYMMDD.pdf``. The two dates are
extracted from the email body text.

Setup:
1. Enable the Gmail API for your Google account and download the
   OAuth credentials file as ``credentials.json``.
2. Install dependencies::

    pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

3. Run the script. The first run opens a browser to authorize access
   and stores the token in ``token.json``.
"""

from __future__ import annotations

import os
import base64
import re
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Modify access is required to mark messages as read
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def get_gmail_service():
    """Authenticate and return a Gmail API service resource."""
    creds: Credentials | None = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def extract_date_range(text: str) -> tuple[str, str] | None:
    """Return start and end dates as YYYYMMDD strings found in text or None."""
    pattern = r"(\d{1,2} [A-Za-z]+ \d{4})\s*[–-]\s*(\d{1,2} [A-Za-z]+ \d{4})"
    match = re.search(pattern, text)
    if not match:
        return None
    try:
        start = datetime.strptime(match.group(1), "%d %B %Y").strftime("%Y%m%d")
        end = datetime.strptime(match.group(2), "%d %B %Y").strftime("%Y%m%d")
    except ValueError:
        return None
    return start, end


def get_message_body(payload: dict) -> str:
    """Decode the HTML part of an email payload."""
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/html" and part.get("body", {}).get(
                "data"
            ):
                data = part["body"]["data"]
                return base64.urlsafe_b64decode(data).decode()
            elif part.get("parts"):
                text = get_message_body(part)
                if text:
                    return text
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode()
    return ""


def download_payslips(
    query: str = "is:unread subject:'Payslip for Zhu-Rong Zheng for Week ending'"
) -> None:
    service = get_gmail_service()

    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])

    for msg in messages:
        msg_detail = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="full")
            .execute()
        )

        body_text = get_message_body(msg_detail["payload"])
        date_range = extract_date_range(body_text)
        if not date_range:
            save_name = "PaySlip_unknown.pdf"
        else:
            start, end = date_range
            save_name = f"PaySlip {start} - {end}.pdf"

        for part in msg_detail["payload"].get("parts", []):
            filename = part.get("filename")
            if not filename or not filename.lower().endswith(".pdf"):
                continue
            att_id = part["body"].get("attachmentId")
            if not att_id:
                continue
            attachment = (
                service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=msg["id"], id=att_id)
                .execute()
            )
            data = base64.urlsafe_b64decode(attachment["data"])
            Path(save_name).write_bytes(data)
            print(f"Saved {save_name}")

        # Mark the message as read
        service.users().messages().modify(
            userId="me",
            id=msg["id"],
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()


if __name__ == "__main__":
    download_payslips()
