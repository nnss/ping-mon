import datetime
import logging

import flask
import jinja2
import ping3
from apscheduler.schedulers import SchedulerAlreadyRunningError
from apscheduler.schedulers.background import BackgroundScheduler
from pydblite import Base


class Config(object):
    SCHEDULER_API_ENABLED = True


def valid_ip(ip):
    """
    :type ip: str
    :rtype: str
    """
    def is_v4(s):
        try:
            return str(int(s)) == s and 0 <= int(s) <= 255
        except:
            return False

    def is_v6(s):
        if len(s) > 4:
            return False
        try:
            return int(s, 16) >= 0 and s[0] != '-'
        except:
            return False

    if ip.count(".") == 3 and all(is_v4(i) for i in ip.split(".")):
        return "IPv4"
    if ip.count(":") == 7 and all(is_v6(i) for i in ip.split(":")):
        return "IPv6"
    return "Neither"


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

    def add_ping_host(self, host):
        self.ips.append(host)
        return self

    def remove_ping_host(self, host):
        print("removing " + host)
        self.ips.remove(host)
        return self

    def jobs(self):
        """ For each IP defined runs the command (ping -c1)."""
        if len(self.ips) == 0:
            return self
        for ip in self.ips:
            dt = datetime.datetime.now()
            time_spent = ping3.ping(ip, unit="ms")
            if time_spent is not None:
                logging.info("for " + ip + " time is " + str(time_spent))
                self.save(ip, str(time_spent), dt)
            else:
                self.save(ip, "-50", dt)
        return self

    def save(self, ip='', result='', dt=datetime.datetime.now()):
        """ Saves the info in the DB. returns nothing'"""
        self.db.insert(ip, result, str(dt))
        self.db.commit()
        return


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

app = flask.Flask(__name__)
db = Base('db_ping.pdl')

if db.exists():
    logging.info("db exists, just opening")
    db.open()
else:
    logging.info("creating DB")
    db.create('host', 'result', 'datetime', mode='open')
    db.commit()
    db.open()

pm = PingMon(dbh=db, debug=False)
sched = BackgroundScheduler()
job = sched.add_job(pm.jobs, 'interval', minutes=1)

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
                  text: 'Matias "nnss" Palomec',
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
                text: 'time in ms'
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
                    text: 'Time'
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
    return flask.redirect("/static/" + path)
    # return flask.send_from_directory('static', path)


@app.route("/status")
def status():
    global sched
    ret = "<h1>Jobs</h1><pre>" + str(sched.print_jobs()) + "</pre><br />"
    ret += "<pre>" + str(sched.get_jobs()) + "</pre><br />\n"
    ret += "<h1>State</h1><pre>" + str(sched.state) + " (0 -> stopped/1 -> running/2 -> pausaed)</pre><br />"
    return tmpl.render(body=ret)


@app.route("/config/", methods=['GET', 'POST'])
def general_config():
    global job
    ip = flask.request.args.get("ip", None)
    action = flask.request.args.get("action", None)
    remove = flask.request.args.get("remove", None)
    if ip == "":
        ip = None
    if action == "remove":
        print("remove is " + remove)
        pm.remove_ping_host(remove)
        msg = remove + " was removed"
        return flask.redirect("/config/")
    if ip is not None:
        if ip not in pm.ips:
            if valid_ip(ip) == 'Neither':
                msg = ""
            pm.add_ping_host(ip)
            job.remove()
            job = sched.add_job(pm.jobs, 'interval', minutes=1)
            # sched.shutdown()
            try:
                sched.start()
            except SchedulerAlreadyRunningError:
                print("Was already running")
            print(sched.state)
        return flask.redirect("/config/")
    if pm.ips is not None and ip is not None and ip in pm.ips:
        return tmpl.render(body="""</head><body><h1>IP already added</h1></body></html>""")
    ret = """<h1>Add IP to monitor</h1>
    <form action="/config" method="get"><label>ip</label><input type="text" name="ip" /><input type="submit"></form>
    <br /><h1>Alreaddy added</h1>
    """
    for ip in pm.ips:
        ret += "<form action='/config' method='get'><label>" + str(ip)
        ret += "</label>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type='submit' name='action' value='remove'>"
        ret += "<input type='hidden' name='remove' value='" + str(ip) + "'></form>\n"
    ret += "\n"
    return tmpl.render(body=ret)


if __name__ == "__main__":
    sched.start()
    print(str(sched.get_jobs()))
    app.run(host="0.0.0.0")
