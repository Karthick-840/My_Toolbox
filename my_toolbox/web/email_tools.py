"""IMAP helper for downloading email attachments."""

import email
import imaplib
import os


def search_emails_with_attachments(
    username,
    password,
    folders=("INBOX",),
    download_dir="attachments",
    host="imap.live.com",
):
    """Yield the path of each attachment saved from messages that have one."""
    mail = imaplib.IMAP4_SSL(host)
    mail.login(username, password)
    os.makedirs(download_dir, exist_ok=True)
    try:
        for folder in folders:
            mail.select(folder)
            _, data = mail.search(None, "(HASATTACHMENT)")
            for num in data[0].split():
                _, msg_data = mail.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                for part in msg.walk():
                    filename = part.get_filename()
                    if filename:
                        filepath = os.path.join(download_dir, os.path.basename(filename))
                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        yield filepath
    finally:
        mail.logout()
