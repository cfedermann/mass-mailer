# -*- coding: utf-8 -*-
"""
Author: Christian Federmann <cfedermann@gmail.com>
Version: 2013-03-15

Usage: $ mass_mailer.py [--dry-run] <config.ini> <mail  |txt> <emails.csv>

Sends an individualised version of mail.html|txt to all recipient email
addresses contained in emails.csv;  configuration details such as mail server
or header fields are read from config.ini.

The following fields inside config.ini are required:

  SMTP=smtp.example.org
  FROM=someone@example.org
  SUBJECT=Mails without subject would not make sense, right?!

There also are some optional settings:

  REPLY-TO=someone@example.org (defaults to FROM address)
  BCC=someone-to-get-bcc-copies@example.org
  FIRST_LASTNAME=Sir or Madam

The mail.html|txt file may contain HTML markup and should be saved in UTF-8
encoding;  there is one "special" placeholder {{FIRST_LASTNAME}} which can be
used to insert the personalised recipient name into the email.  If the name
cannot be resolved from the email address, the script will use FIRST_LASTNAME
from config.ini, iff available, defaulting to "Sir or Madam" otherwise.

A template ending with extension ".txt" triggers sending of plain text emails.

Email addresses should be given in comma-separated list form, e.g.:

  firstname,lastname,email
  John,Doe,john@example.org
  ,,noname@example.org

You can use the optional "--dry-run" flag to run the script in testing mode
which will do everything except sending out the actual emails.

It is a wise idea to test any new mail.html|txt or config.ini with your own
email address first.  The author does not any responsibility for emails sent
out with this tool.  By using the script, you accept this.

Code is available under BSD-style terms.  See LICENSE for more information.

"""
import smtplib
import sys
from base64 import b64decode
from email.mime.text import MIMEText
from traceback import format_exc

DRY_RUN = False
CONFIG = {}
TEMPLATE = None
EMAILS = []


def usage():
    """
    Returns usage information for mass_mailer.py.
    """
    return (
        """Usage: $ mass_mailer.py [--dry-run] <config.ini> """
        """<mail.html|txt> <emails.csv>

Sends an individualised version of mail.html|txt to all recipient email
addresses contained in emails.csv;  configuration details such as mail server
or header fields are read from config.ini.

You can use the optional "--dry-run" flag to run the script in testing mode
which will do everything except sending out the actual emails.

Code is available under BSD-style terms.  See LICENSE for more information.
    """
    )


def load_config(filename):
    """
    Loads configuration from the given .ini file.

    The following fields inside config.ini are required:

      SMTP=smtp.example.org
      FROM=someone@example.org
      SUBJECT=Mails without subject would not make sense, right?!

    There also are some optional settings:

      REPLY-TO=someone@example.org (defaults to FROM address)
      BCC=someone-to-get-bcc-copies@example.org
      FIRST_LASTNAME=Sir or Madam

    """
    _config = {}
    assert filename.endswith(".ini")
    with open(filename) as ini_file:
        for line in ini_file:
            option = line.decode("utf-8").strip().split("=")

            # We simply ignore comments and groups inside the .ini file.
            if len(option) == 2:
                key = option[0].strip().upper()
                value = option[1].strip()
                _config[key] = value

        # Check that all required keys are available.
        for key in ("SMTP", "FROM", "SUBJECT"):
            assert key in _config.keys()

        # Fallback to default values for REPLY-TO and FIRST_LASTNAME if they
        # are not available from the given configuration dictionary.
        if "REPLY-TO" not in _config.keys():
            _config["REPLY-TO"] = _config["FROM"]

        if "FIRST_LASTNAME" not in _config.keys():
            _config["FIRST_LASTNAME"] = "Sir or Madam"

    return _config


def load_template(filename):
    """
    Loads the email template from the given .html|txt file.

    The mail.html|txt file may contain HTML markup and should be saved in
    UTF-8 encoding;  there is one "special" placeholder {{FIRST_LASTNAME}}
    which can be used to insert the personalised recipient name into the
    email.  If the name cannot be resolved from the email address, the script
    will use FIRST_LASTNAME from config.ini, iff available, defaulting to "Sir
    or Madam" otherwise.

    """
    _template = None
    _mime_type = None
    assert filename.endswith(".html") or filename.endswith(".txt")

    if filename.endswith(".html"):
        _mime_type = "html"
    elif filename.endswith(".txt"):
        _mime_type = "plain"

    with open(filename) as _file:
        _template = _file.read()
    _template = _template.decode("utf-8")

    return _template, _mime_type


def load_emails(filename):
    """
    Loads the email addresses from the given .csv file.

    Email addresses should be given in comma-separated list form, e.g.:

      firstname,lastname,email
      John,Doe,john@example.org
      ,,noname@example.org

    """
    _emails = []
    assert filename.endswith(".csv")
    with open(filename) as csv_file:
        for _line in csv_file:
            # Remove trailing newline character and any enclosing whitespace.
            line = _line.decode("utf-8").strip()

            # Ignore comment lines.
            if line.startswith("#"):
                continue

            # Split line into data items and make sure that email contains @.
            data = line.split(",")
            assert len(data) == 3 and "@" in data[2], line

            # If firstname and lastname are not available, store None instead.
            _emails.append(
                (
                    data[0].strip() or None,
                    data[1].strip() or None,
                    data[2].strip(),
                )
            )

    return _emails


if __name__ == "__main__":
    # Initialise configuration, email template, and list of emails.
    try:
        if sys.argv[1].lower() == "--dry-run":
            DRY_RUN = True

        CONFIG = load_config(sys.argv[1 + int(DRY_RUN)])
        TEMPLATE, MIME_TYPE = load_template(sys.argv[2 + int(DRY_RUN)])
        EMAILS = load_emails(sys.argv[3 + int(DRY_RUN)])
        print("\nInit. Configuration, email template, and emails loaded.")

    # IndexError
    # AssertionError
    # UnicodeDecodeError (?)
    # open() raises which exceptions (?)
    except:
        print("\nFail. An error occured:\n")
        print(format_exc())
        print(usage())
        sys.exit(-1)

    # We keep track of the number of errors and used email addresses.
    ERRORS = 0
    SKIPPED = 0
    USED_EMAIL_ADDRESSES = set()

    # Send out individualised emails to all recipients inside EMAILS.
    for recipient in EMAILS:
        email = recipient[2]

        # Don't send the email twice!
        if email in USED_EMAIL_ADDRESSES:
            print(u"Skip. Duplicate email address: {0}".format(email))
            SKIPPED += 1
            continue

        USED_EMAIL_ADDRESSES.add(email)

        # Build proper FIRST_LASTNAME template variable contents.
        if recipient[0]:
            FIRST_LASTNAME = u"{0} {1}".format(recipient[0], recipient[1])
            FIRST_LASTNAME = FIRST_LASTNAME.strip()

        else:
            FIRST_LASTNAME = CONFIG["FIRST_LASTNAME"]

        # Render TEMPLATE and create corresponding MIMEText message from it.
        message = TEMPLATE.replace("{{FIRST_LASTNAME}}", FIRST_LASTNAME)
        msg = MIMEText(message, MIME_TYPE, "utf-8")
        msg["From"] = CONFIG["FROM"]
        msg["Reply-To"] = CONFIG["REPLY-TO"]
        msg["To"] = email
        msg["Subject"] = CONFIG["SUBJECT"]

        # Add BCC To recipients list, iff available.
        recipients = [email]
        if "BCC" in CONFIG.keys():
            recipients.append(CONFIG["BCC"])

        try:
            # Try sending out the email message to recipients list.
            if not DRY_RUN:
                s = smtplib.SMTP(CONFIG["SMTP"])
                s.sendmail(CONFIG["FROM"], recipients, msg.as_string())
                s.quit()
                print(u"Sent. Recipient email address: {0}".format(email))

            # Except when running a --dry-run where we just print debug info.
            else:
                print(
                    "Test. Would now run s.sendmail({0}, {1}, "
                    "msg.as_string())".format(CONFIG["FROM"], recipients)
                )

                print(
                    "Data. {0!r}\n--\n".format(
                        b64decode(msg.get_payload())
                    )
                )

        # SMTPRecipientsRefused
        # SMTPHeloError
        # SMTPSenderRefused
        # SMTPDataError
        # SMTPNotSupportedError
        # pylint: disable-msg=W0703
        except smtplib.SMTPException as error_msg:
            ERRORS += 1
            print(u"Fail. Error when sending email to {0}".format(email))
            print("      {0}".format(error_msg))

    print(
        "Done. {0} errors, {1} skipped emails when trying to send {2} "
        "messages.\n".format(ERRORS, SKIPPED, len(EMAILS))
    )
