# About the program


This is a simple Flack python script, by now it only contains 1 page. This 
shows the result of the ping checks, getting the data from a python DB
(json format), and showing a simple graph of the last day.

The ping is done with ApScheduler to 8.8.8.8 and to my router (172.27.1.1).
 This should be configurable, but by now is just hardcoded.

This is intended to be really simple script, check 1 or 2 hosts at most. The
reason for me to do this is to monitor the internet connection. I checked
some programs, but neither of what I found was just a simple ping to a host
that shows the results in graphics and in a single program (well, some extra
dependencies and the DB to store data).

# ToDo


* tidy code
* add inline doc for auto-document the script
* improve HTML
  * use templates to improve look and feel
  * make another page to view all data
  * add a stop reload in the graphic page (or something in the GET)
* make configurable via web (store data also in the DB)
* (opt) decide if this should be just 1 script and make the DB
  in memory and lost historical data or add some parameters to
  view historical data.
