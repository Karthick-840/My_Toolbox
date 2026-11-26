# src/email_processor.py
import os
import email
import imaplib
import src.config as config  # Import config from src

def search_emails_with_attachments():
    mail = imaplib.IMAP4_SSL("imap.live.com")
    mail.login(config.EMAIL_CREDENTIALS["username"], config.EMAIL_CREDENTIALS["password"])

    for folder in config.EMAIL_FOLDERS:
        mail.select(folder)
        _, data = mail.search(None, '(HASATTACHMENT)')
        for num in data[0].split():
            _, data = mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            for part in msg.walk():
                if part.get_filename():
                    filename = part.get_filename()
                    filepath = os.path.join(config.DATA_ATTACHMENT_PATH, filename) #changed path.
                    os.makedirs(config.DATA_ATTACHMENT_PATH, exist_ok=True) #make sure folder exists.
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    yield filepath
    mail.close()
    mail.logout()