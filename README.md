# About the program


This is a simple ping monitoring app made in Flask (python) that
uses pure python modules, so it would be used under windows and
*nix where python runs, and as a docker image. It only keeps the
last 24 hours, timeouts are shown as -50ms in the times. Besides
the raw data, there is a simple graphic that shows the last 24 hours
using hicharts.

The ping is done with ApScheduler to and is configured via /config URL. It
can be 1 or more IPs and each one is showed at the home page.

This is intended to be really simple script, the main reason for this
program was to monitor the internet of my home, and to understand
why was slow (lost packages, bad wify, etc)

This is not  to be a full monitoring tool, just an ICMP ping
with a small history (24 hours).

# ToDo

* tidy code
* add inline doc for auto-document the script
* store IPs in the DB
* add housekeeping:
  * clean old DB entries when program starts and each X hours
* add about page with some help to the WEB, Copyright and 
  other info.

Docker:
* move the DB to a mountable volume

## JS installer

* https://code.jquery.com/jquery-1.12.4.min.js
* 