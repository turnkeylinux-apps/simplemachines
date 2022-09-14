#!/usr/bin/python3
"""Set SimpleMachines admin password, email and domain to serve

Option:
    --pass=     unless provided, will ask interactively
    --email=    unless provided, will ask interactively
    --domain=   unless provided, will ask interactively
                DEFAULT=www.example.com
"""

import sys
import getopt
from libinithooks import inithooks_cache

import hashlib

from libinithooks.dialog_wrapper import Dialog
from mysqlconf import MySQL
import subprocess

def usage(s=None):
    if s:
        print("Error:", s, file=sys.stderr)
    print("Syntax: %s [options]" % sys.argv[0], file=sys.stderr)
    print(__doc__, file=sys.stderr)
    sys.exit(1)

DEFAULT_DOMAIN="www.example.com"

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "h",
                                       ['help', 'pass=', 'email=', 'domain='])
    except getopt.GetoptError as e:
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

    inithooks_cache.write('APP_EMAIL', email)

    if not domain:
        if 'd' not in locals():
            d = Dialog('TurnKey Linux - First boot configuration')

        domain = d.get_input(
            "SimpleMachines Domain",
            "Enter the domain to serve SimpleMachines.",
            DEFAULT_DOMAIN)

    if domain == "DEFAULT":
        domain = DEFAULT_DOMAIN

    inithooks_cache.write('APP_DOMAIN', domain)

    hash = hashlib.sha1(('admin' + password).encode('utf8')).hexdigest()

    m = MySQL()
    m.execute('UPDATE simplemachines.members SET passwd=%s WHERE member_name=\"admin\";', (hash,))
    m.execute('UPDATE simplemachines.members SET email_address=%s WHERE member_name=\"admin\";', (email,))

    m.execute('UPDATE simplemachines.settings SET value=%s WHERE variable=\"smileys_url\";', (f"http://{domain}/Smileys"))
    m.execute('UPDATE simplemachines.settings SET value=%s WHERE variable=\"avatar_url\";', (f"http://{domain}/avatars",))
    
    m.execute('UPDATE simplemachines.themes SET value=%s WHERE variable=\"theme_url\" AND id_theme=1;', (f"http://{domain}/Themes/default",))
    m.execute('UPDATE simplemachines.themes SET value=%s WHERE variable=\"images_url\" AND id_theme=1;', (f"http://{domain}/Themes/default/images",))
    m.execute('UPDATE simplemachines.themes SET value=%s WHERE variable=\"theme_url\" AND id_theme=2;', (f"http://{domain}/Themes/core",))
    m.execute('UPDATE simplemachines.themes SET value=%s WHERE variable=\"images_url\" AND id_theme=2;', (f"http://{domain}/Themes/core/images",))

    config = "/var/www/simplemachines/Settings.php"
    subprocess.run(["sed", "-i", f"s|boardurl.*|boardurl = 'http://{domain}';|", config])
    subprocess.run(["sed", "-i", f"s|webmaster_email.*|webmaster_email = '{domain}';|", config])


if __name__ == "__main__":
    main()

