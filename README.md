mass-mailer
===========

Python-based mass mailer script

__Author:__ Christian Federmann <cfedermann@dfki.de>

__Version:__ 2012-09-25

    Usage: $ mass_mailer.py [--dry-run] <config.ini> <mail.html|txt> <emails.csv>

Sends an individualised version of `mail.html|txt` to all recipient email
addresses contained in `emails.csv`;  configuration details such as mail server
or header fields are read from `config.ini`.

The following fields inside `config.ini` are required:

    SMTP=smtp.example.org
    FROM=someone@example.org
    SUBJECT=Mails without subject would not make sense, right?!

There also are some optional settings:

    REPLY-TO=someone@example.org (defaults to FROM address)
    BCC=someone-to-get-bcc-copies@example.org
    FIRST_LASTNAME=Sir or Madam

The `mail.html|txt` file may contain HTML markup and should be saved in UTF-8
encoding;  there is one "special" placeholder `{{FIRST_LASTNAME}}` which can be
used to insert the personalised recipient name into the email.  If the name
cannot be resolved from the email address, the script will use `FIRST_LASTNAME`
from `config.ini`, iff available, defaulting to `"Sir or Madam"` otherwise.

A template ending with extension ".txt" triggers sending of plain text emails.

Email addresses should be given in comma-separated list form, e.g.:

    # firstname,lastname,email
    John,Doe,john@example.org
    ,,noname@example.org

You can use the optional `"--dry-run"` flag to run the script in testing mode
which will do everything except sending out the actual emails.

It is a wise idea to test any new `mail.html|txt` or `config.ini` with your own
email address first.  The author does not any responsibility for emails sent
out with this tool.  By using the script, you accept this.

Code is available under BSD-style terms.  See [LICENSE][1] for more information.

[1]: https://raw.github.com/cfedermann/mass-mailer/master/LICENSE