import datetime
import os
import re
import subprocess
import sys
from functools import wraps
from urllib.error import URLError
from urllib.request import urlopen

import time
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, send_from_directory
from pydblite import Base


class Config(object):
    SCHEDULER_API_ENABLED = True


class PingMon:
    def __init__(self, dbh: Base, debug: object = True, ips: [] = ['8.8.8.8', '172.27.1.1']) -> None:
        """ The initialization gets:
        * dbh (Base object)
        * debug
        * ip (array)
        In a future, could get also cmd
        """
        self.options_from_ini_file = ""
        self.debug = debug
        self.c_error = ''
        self.ips = ips
        self.db = dbh
        self.cmd = 'ping -c1'

    def jobs(self):
        """ For each IP defined runs the command (ping -c1)."""
        for ip in self.ips:
            dt = datetime.datetime.now()
            my_out = self.job(self.cmd + " " + ip)
            search = re.search(r'.*ttl=\d+\s+time=(\S+)\s.*', my_out, re.MULTILINE)
            if search:
                self.save(ip, search.group(1), str(dt))
            else:
                self.save(ip, "-50", str(dt))
        return self

    def save(self, ip='', result='', dt=datetime.datetime.now()):
        """ Saves the info in the DB. returns nothing'"""
        self.db.insert(ip, result, str(dt))
        self.db.commit()
        return

    def job(self, cmd):
        """ The job to execute (cmd + host) and return the """
        # self.pd("Inside JOB!")
        my_cmd = cmd.split(' ')
        # self.pd("proc " + str(my_cmd))
        output, error = subprocess.Popen(my_cmd,
                                         shell=False,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE).communicate()
        output = output.decode('utf-8').strip()
        # self.pd(output)
        if output == "":
            sys.stderr.write("ERROR: %s" % error)
            self.c_error = error
            return None
        else:
            return output

    def retry(exception_to_check, tries=4, delay=3, backoff=2, logger=None):
        def deco_retry(f):
            @wraps(f)
            def f_retry(*args, **kwargs):
                mtries, mdelay = tries, delay
                while mtries > 1:
                    try:
                        return f(*args, **kwargs)
                    except exception_to_check as e:
                        msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                        if logger:
                            logger.warning(msg)
                        else:
                            print(msg)
                        time.sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff
                return f(*args, **kwargs)

            return f_retry  # true decorator

        return deco_retry

    @retry(URLError, tries=4, delay=3, backoff=2)
    def get_url(self, url):
        po = re.compile(r".*/([^/]+)$").match(url)
        if po:
            if os.path.isfile("cache/" + po.group(1)):
                return open("cache/" + po.group(1), "r").read()
            else:
                ca = urlopen(url).read()
                local = open("cache/" + po.group(1), "w")
                local.write(ca)
                return ca
        else:
            return urlopen(url).read()

    def pd(self, msg=None):
        if msg is not None and self.debug:
            print("---" + str(msg))


app = Flask(__name__)
db = Base('db/ping.pdl')

if db.exists():
    db.open()
else:
    db.create('host', 'result', 'datetime', mode='open')
    db.commit()
    db.open()

pm = PingMon(dbh=db, debug=False)
sched = BackgroundScheduler()
job = sched.add_job(pm.jobs, 'interval', minutes=1)
sched.start()


@app.route('/')
def hello_world():
    carry = ""
    for ip in pm.ips:
        carry += "<li><a href='/by_host/" + ip + "'>by host " + ip + "</a></li>"

    return """
<html>
<head><title>SimpleMonPing</title>
</head>
<body>
<h1>Options</h1>
<ul>
""" + carry + """
</ul>
<footer>""" + str(sched.state) + " " + str(sched.get_jobs()) + """</footer>
</body>
</html>    
"""


@app.route('/by_host/<ip>')
def by_host(ip='8.8.8.8'):
    carry = ''
    carry_title = ""
    for my_ip in pm.ips:
        carry_title += "<li><a href='/by_host/" + my_ip + "'>by host " + my_ip + "</a></li>"
    carry_lost = ""

    results = db(host=ip)
    results = sorted(results, key=lambda kv: kv['datetime'])

    for result in results:
        t = datetime.datetime.strptime(result['datetime'], "%Y-%m-%d %H:%M:%S.%f")
        if t > (datetime.datetime.now() - datetime.timedelta(days=1)):
            # carry += '<tr><td>' + str(result['host']) + '</td><td>' + str(result['datetime']) + '</td><td>' + \
            #           str(result['result']) + '</td></tr>'
            carry += '<tr><td>' + str(result['datetime']) + '</td><td>' + str(result['result']) + '</td></tr>'
    ret = """
    <html>
    <head><title>SimpleMonPing</title>
     <meta http-equiv="refresh" content="30">
    <script src="/js/jquery-1.12.1.min.js"></script>
    <script src="/js/highcharts.js"></script>
    <script src="/js/highcharts-more.js"></script>
    <script src="/js/exporting.js"></script>
    <script src="/js/data.js"></script>
    <script src="/js/export-data.js"></script>
    <script type='text/javascript'>
//<![CDATA[
$(document).ready(function(){
  $('#datatable').hide();
  $('button').click(function(){
    $('table').toggle();
    if($('button').html()!="hide table"){
      $('button').html('hide table');
    }else{
      $('button').html('show table');
    }
 });
});
$(function () {
    $('#container').highcharts({
        data: {
            table: 'datatable',
            switchRowsAndColumns: false
        },
        chart: {
            type: 'line',
            zoomType: 'x'
        },
        credits: {
                  text: 'oops support team',
                  href: 'http://nnss.com.ar',
                  style: {
                       color: '#fe8503',
                       fontSize: '9px'
                  }
        },
        legend: {
                 enable: true
        },
        yAxis: {
            allowDecimals: false,
            title: {
                text: 'host'
            },
                plotLines:[{
                            value:0,
                            color: '#ff0000',
                            width:2,
                            zIndex:4,
                }],
        },
        xAxis: {
            title: {
                    text: 'xAxis'
                    },
        },
        title: {
            text: 'Data from PING'
        },
        tooltip: {
            formatter: function () {
                    tmpTime = new Date(parseInt(this.point.x) + 10800000);
                    return '<b>' + this.series.name + '</b><br/>y: ' +
                          this.point.y + ' x: ' + tmpTime.toString();
            }
        }
    });
});
//]]
  </script>
    <style>
.rounded-corner{font-family:"Lucida Sans Unicode", "Lucida Grande",
    Sans-Serif;font-size:12px;width:480px;text-align:left;
    border-collapse:collapse;margin:20px;}
.rounded-corner thead th.rounded-company{background:#b9c9fe ;}
.rounded-corner thead th.rounded-q4{background:#b9c9fe ;}
.rounded-corner th{font-weight:normal;font-size:13px;color:#039;background:#ff7f00;padding:8px;}
.rounded-corner td{background:#ffd4aa;border-top:1px solid #fff;color:#669;padding:8px;}
.rounded-corner tfoot td.rounded-foot-left{background:#e8edff ; }
.rounded-corner tfoot td.rounded-foot-right{background:#e8edff ; }
.rounded-corner tbody tr:hover td{background:#d0dafd;}
table tr:first-child th:first-child, table.Info tr:first-child td:first-child { border-top-left-radius: 16px; }
table tr:first-child th:last-child, table.Info tr:first-child td:last-child { border-top-right-radius: 16px; }
table tr:last-child td:first-child { border-bottom-left-radius: 16px; }
table tr:last-child td:last-child { border-bottom-right-radius: 16px; }
  </style>
    </head>
    <body>
    <h1>list for """ + ip + """</h1>
    <ul>""" + carry_title + """
    <div id='container' style='min-width: 310px; height: 400px; margin: 0 auto'></div>
    <div style='position: relative; left: 50%; widh: 100%;'><button>show table</div>
    <table id='datatable' class='rounded-corner'>
    <thead><tr><th>date time</th><th>result</th></tr></thead>
    <tbody>
    """ + str(carry) + """
    </tbody>
    </table>
    <footer>Schedule state: """ + str(sched.state) + \
          "<br /> Last updated:" + str(datetime.datetime.now().isoformat()) + """<br />
          Stats LOST: """ + "" + """
    </footer>
    </body>
    </html>    
    """
    return ret


@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('static', path)


if __name__ == "__main__":
    sched.start()
    print(str(sched.get_jobs()))
    app.run()
