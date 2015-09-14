SimpleMachines - Forum system
=============================

`SimpleMachines`_ provides an easy to use forum with many powerful
features for you as well as your users. It features a powerful Package
Manager, allowing you to quickly apply any of the hundreds of
modifications in our database, as well as a variety of custom themes
that change the way your site looks.

This appliance includes all the standard features in `TurnKey Core`_,
and on top of that:

- SimpleMachines configurations:
   
   - Installed from upstream source code to /var/www/simplemachines

- SSL support out of the box.
- `Adminer`_ administration frontend for MySQL (listening on port
  12322 - uses SSL).
- Postfix MTA (bound to localhost) to allow sending of email (e.g.,
  password recovery).
- Webmin modules for configuring Apache2, PHP, MySQL and Postfix.

Credentials *(passwords set at first boot)*
-------------------------------------------

-  Webmin, SSH, MySQL, Adminer: username **root**
-  SimpleMachines: username **admin**


.. _SimpleMachines: http://www.simplemachines.org/
.. _TurnKey Core: https://www.turnkeylinux.org/core
.. _Adminer: http://www.adminer.org/
