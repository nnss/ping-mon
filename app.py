import datetime
import os
import platform
import re
import subprocess
import sys
import time
from functools import wraps
from urllib.error import URLError
from urllib.request import urlopen
# from flask import Flask, send_from_directory, redirect
import flask
import jinja2
from apscheduler.schedulers.background import BackgroundScheduler
from pydblite import Base


class Config(object):
    SCHEDULER_API_ENABLED = True


class PingMon:
    def __init__(self, dbh: Base, debug: object = True, ips=None) -> None:
        """ The initialization gets:
        * dbh (Base object)
        * debug
        * ip (array)
        In a future, could get also cmd
        """
        if ips is None:
            ips = list()
        self.options_from_ini_file = ""
        self.debug = debug
        self.c_error = ''
        self.ips = ips
        self.db = dbh
        param = '-n 1' if platform.system().lower() == 'windows' else '-c1'
        self.cmd = 'ping' + " " + param

    def add_ping_host(self, host):
        self.ips.append(host)
        return self

    def jobs(self):
        """ For each IP defined runs the command (ping -c1)."""
        if len(self.ips) == 0:
            return self
        for ip in self.ips:
            dt = datetime.datetime.now()
            my_out = self.job(self.cmd + " " + ip)
            if platform.node():
                search = re.search(r'.*Media = (\d+)ms.*', my_out, re.MULTILINE)
            else:
                search = re.search(r'.*ttl=\d+\s+time=(\S+)\s.*', my_out, re.MULTILINE)
            if search:
                self.save(ip, search.group(1), dt)
            else:
                self.save(ip, "-50", dt)
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
        # print("cmd is " + my_cmd)
        output, error = subprocess.Popen(my_cmd,
                                         shell=False,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE).communicate()
        try:
            output = output.decode('utf-8').strip()
        except UnicodeDecodeError:
            output = str(output).strip()
        # self.pd(output)
        print("OUTPUT " + str(output))
        if output == "":
            sys.stderr.write("ERROR: %s" % error)
            self.c_error = error
            return None
        else:
            return output

    def retry(exception_to_check, tries: object = 4, delay: object = 3, backoff: object = 2,
              logger: object = None) -> object:
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


app = flask.Flask(__name__)
db = Base('db_ping.pdl')

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

base_html = """
<html>
    <head><title>ping-mon</title>
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
                  text: 'Maias "nnss" Palomec',
                  href: 'http://nnss.net.ar',
                  style: {
                       color: '#fe8503',
                       fontSize: '9px'
                  }
        },
        legend: {
                 enable: false
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
                    text: 'Date'
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
.main {   padding: 16px;
  margin-top: 30px;
  height: 1500px; /* Used in this example to enable scrolling */
}
.topnav {   overflow: hidden;
  background-color: #333;
  position: fixed;
  top: 0;
  width: 100%; }
.topnav a { float: left; display: block; color: #f2f2f2; text-align: center;padding: 14px 16px; text-decoration: none; }
.topnav a:hover { background-color: #ddd; color: black;}
  </style>
    </head>
    <body>
    <div class="topnav">
      <a href="/">Home</a>
      <a href="/config">Config</a>
      <a href="/status">Status</a>
    </div>
    <div class="main">
    <h1>{{title}}</h1>

    <ul>
    {{body}}
    </div>
    </body>
    </html>
"""
tmpl = jinja2.Template(base_html)


@app.route('/')
def home():
    carry = ""
    if pm.ips is None:
        return flask.redirect("/config")
    for ip in pm.ips:
        carry += "<li><a href='/by_host/" + ip + "'>by host " + ip + "</a></li>"

    ret = """
<h1>Options</h1>
<ul>
""" + carry + """
</ul>
<footer>""" + str(sched.state) + " " + str(sched.get_jobs()) + """</footer>  
"""
    return tmpl.render(body=ret)


@app.route('/by_host/<ip>')
def by_host(ip='8.8.8.8'):
    carry = ''
    carry_title = ""
    for my_ip in pm.ips:
        carry_title += "<li><a href='/by_host/" + my_ip + "'>by host " + my_ip + "</a></li>"

    results = db(host=ip)
    results = sorted(results, key=lambda kv: kv['datetime'])

    for result in results:
        t = datetime.datetime.strptime(result['datetime'], "%Y-%m-%d %H:%M:%S.%f")
        if t > (datetime.datetime.now() - datetime.timedelta(days=1)):
            # carry += '<tr><td>' + str(result['host']) + '</td><td>' + str(result['datetime']) + '</td><td>' + \
            #           str(result['result']) + '</td></tr>'
            carry += '<tr><td>' + str(result['datetime']) + '</td><td>' + str(result['result']) + '</td></tr>'
    ret = """
    <div id='container' style='min-width: 310px; height: 400px; margin: 0 auto'></div>
    <div style='position: relative; left: 50%; widh: 100%;'><button>show table</div>
    <table id='datatable' class='rounded-corner'>
    <thead><tr><th>date time</th><th>result</th></tr></thead>
    <tbody>""" + carry + """</tbody>
    </table>
    <footer>Schedule state: """ + str(sched.state) + \
          "<br /> Last updated:" + str(datetime.datetime.now().isoformat()) + """<br />
    </footer>   
    """
    return tmpl.render(title="Home", body=ret)


@app.route('/js/<path:path>')
def send_js(path):
    return flask.send_from_directory('static', path)


@app.route("/status")
def status():
    global sched
    ret = "<h1>Status</h1><pre>" + str(sched.get_jobs()) + "</pre>"
    return tmpl.render(body=ret)


@app.route("/config/", methods=['GET', 'POST'])
def general_config():
    global job
    ip = flask.request.args.get("ip", None)
    if ip == "":
        ip = None
    if ip is not None:
        if ip not in pm.ips:
            pm.add_ping_host(ip)
            job.remove()
            job = sched.add_job(pm.jobs, 'interval', minutes=1)
            # sched.shutdown()
            # sched.start()
            print(sched.state)
        return flask.redirect("/")
    if pm.ips is not None and ip is not None and ip in pm.ips:
        return tmpl.render(body="""</head><body><h1>IP already added</h1></body></html>""")
    ret = """<h1>Add IP to monitor</h1>
    <form action="/config" method="get"><label>ip</label><input type="text" name="ip" /><input type="submit">
    """
    return tmpl.render(body=ret)


if __name__ == "__main__":
    sched.start()
    print(str(sched.get_jobs()))
    app.run(host="0.0.0.0")
