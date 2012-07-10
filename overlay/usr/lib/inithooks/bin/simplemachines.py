#!/usr/bin/python
"""Set SimpleMachines admin password, email and domain to serve

Option:
    --pass=     unless provided, will ask interactively
    --email=    unless provided, will ask interactively
    --domain=   unless provided, will ask interactively
                DEFAULT=www.example.com
"""

import sys
import getopt
import hashlib

from dialog_wrapper import Dialog
from mysqlconf import MySQL
from executil import system

def usage(s=None):
    if s:
        print >> sys.stderr, "Error:", s
    print >> sys.stderr, "Syntax: %s [options]" % sys.argv[0]
    print >> sys.stderr, __doc__
    sys.exit(1)

DEFAULT_DOMAIN="www.example.com"

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "h",
                                       ['help', 'pass=', 'email=', 'domain='])
    except getopt.GetoptError, e:
        usage(e)

    email = ""
    domain = ""
    password = ""
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt == '--pass':
            password = val
        elif opt == '--email':
            email = val
        elif opt == '--domain':
            domain = val

    if not password:
        d = Dialog('TurnKey Linux - First boot configuration')
        password = d.get_password(
            "SimpleMachines Password",
            "Enter new password for the SMF 'admin' account.")

    if not email:
        if 'd' not in locals():
            d = Dialog('TurnKey Linux - First boot configuration')

        email = d.get_email(
            "SimpleMachines Email",
            "Enter email address for the SMF 'admin' account.",
            "admin@example.com")

    if not domain:
        if 'd' not in locals():
            d = Dialog('TurnKey Linux - First boot configuration')

        domain = d.get_input(
            "SimpleMachines Domain",
            "Enter the domain to serve SimpleMachines.",
            DEFAULT_DOMAIN)

    if domain == "DEFAULT":
        domain = DEFAULT_DOMAIN

    hash = hashlib.sha1('admin' + password).hexdigest()

    m = MySQL()
    m.execute('UPDATE simplemachines.members SET passwd=\"%s\" WHERE member_name=\"admin\";' % hash)
    m.execute('UPDATE simplemachines.members SET email_address=\"%s\" WHERE member_name=\"admin\";' % email)

    m.execute('UPDATE simplemachines.settings SET value=\"http://%s/Smileys\" WHERE variable=\"smileys_url\";' % domain)
    m.execute('UPDATE simplemachines.settings SET value=\"http://%s/avatars\" WHERE variable=\"avatar_url\";' % domain)
    
    m.execute('UPDATE simplemachines.themes SET value=\"http://%s/Themes/default\" WHERE variable=\"theme_url\" AND id_theme=1;' % domain)
    m.execute('UPDATE simplemachines.themes SET value=\"http://%s/Themes/default/images\" WHERE variable=\"images_url\" AND id_theme=1;' % domain)
    m.execute('UPDATE simplemachines.themes SET value=\"http://%s/Themes/core\" WHERE variable=\"theme_url\" AND id_theme=2;' % domain)
    m.execute('UPDATE simplemachines.themes SET value=\"http://%s/Themes/core/images\" WHERE variable=\"images_url\" AND id_theme=2;' % domain)

    config = "/var/www/simplemachines/Settings.php"
    system("sed -i \"s|boardurl.*|boardurl = 'http://%s';|\" %s" % (domain, config))
    system("sed -i \"s|webmaster_email.*|webmaster_email = '%s';|\" %s" % (email, config))


if __name__ == "__main__":
    main()

