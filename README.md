# About the program


This is a simple Flack python script, by now it only contains 1 page. This 
shows the result of the ping checks, getting the data from a python DB
(json format), and showing a simple graph of the last day.

The ping is done with ApScheduler to and is configured via /config URL. It
can be 1 or more IPs and each one is showed at the home page.

Now works on windows and *nix. 

This is intended to be really simple script, check 1 or 2 hosts at most. The
reason for me to do this is to monitor the internet connection. I checked
some programs, but neither of what I found was just a simple ping to a host
that shows the results in graphics and in a single program (well, some extra
dependencies and the DB to store data).

# ToDo

* tidy code
* add inline doc for auto-document the script
* store IPs in the DB?
  * remove the file and make it live in memory only?
