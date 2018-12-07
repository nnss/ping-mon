from flask import Flask, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler

import subprocess
import sys
import re
import datetime
from pydblite import Base


class Config(object):
    SCHEDULER_API_ENABLED = True


class PingMon:
    def __init__(self, dbh="", debug=True):
        self.options_from_ini_file = ""
        self.debug = debug
        self.c_error = ''
        self.ips = ['8.8.8.8']
        self.db = dbh

    def jobs(self):
        for ip in self.ips:
            dt = datetime.datetime.now()
            my_out = self.job("ping -c1 " + ip)
            search = re.search(r'.*ttl=\d+\s+time=(\S+)\s.*', my_out, re.MULTILINE)
            if search:
                self.save(ip, search.group(1), dt)
            else:
                self.save(ip, "-50", str(dt))

    def save(self, ip='', result='', dt=str(datetime.datetime.now())):
        self.db.insert(ip, result, str(dt))
        self.db.commit()
        return

    def job(self, cmd):
        # print("Hola Mundo!")
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
    return """
<html>
<head><title>SimpleMonPing</title>
</head>
<body>
<h1>Options</h1>
<ul><li><a href='/by_host'>by host</a></li>
</ul>
<footer>""" + str(sched.state) + " " + str(sched.get_jobs()) + """</footer>
</body>
</html>    
"""


@app.route('/by_host')
def by_host():
    carry = ''
    results = db(host='8.8.8.8')
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
                  text: 'Vizrt support team',
                  href: 'http://www.vizrt.com',
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
            }
        },
        title: {
            text: 'Data from PING'
        },
        tooltip: {
            formatter: function () {
                    return '<b>' + this.series.name + '</b><br/>' +
                          this.point.y + ' ' + this.point.name;
            }
        }
    });
});
//]]
  </script>
    <style>
.rounded-corner{font-family:"Lucida Sans Unicode", "Lucida Grande", Sans-Serif;font-size:12px;width:480px;text-align:left;border-collapse:collapse;margin:20px;}
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
    <h1>list</h1>
    <div id='container' style='min-width: 310px; height: 400px; margin: 0 auto'></div>
    <div style='position: relative; left: 50%; widh: 100%;'><button>show table</div>
    <table id='datatable' class='rounded-corner'>
    <thead><tr><th>date time</th><th>result</th></tr></thead>
    <tbody>
    """ + str(carry) + """
    </tbody>
    </table>
    <footer>Sched state: """ + str(sched.state) + \
          "<br /> Last updated:" + str(datetime.datetime.now().isoformat()) + """
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
