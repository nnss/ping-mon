Abut the program
================

This is a simple Flack python script, by now it only contains 1 page. This 
shows the result of the ping checks, geting the data from a python DB
(json format), and showingi a simple graph of the last day.

The ping is done with ApScheduler to 8.8.8.8. This should be conigurable,
but by now is just hardcoded.

This is mented to be really simple script, check 1 or 2 hosts at most. The
reason for me to do this is to monitor the internet connection. I checked
some programs, but neither of what I found was just a simple ping to a host
that shows the results in graphics and in a single program (well, some extra
depenencies and the DB to store data).

ToDo
====

* tidy code
* add inline doc for auto-document the script
* improve HTML
  * make another page to view all data
  * add a stop reload in the graphic page (or somethingi in the GET)
* make cofigurable via web (store data alson in the DB)
* (opt) use templates to improve look and feel
* (opt) have mor than 1 host to check (via cofig)
* (opt) decide if this should be just 1 script and make the DB
  in memory and lost historical data.
