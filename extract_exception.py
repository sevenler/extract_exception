import os
import smtplib
import re

from email import encoders
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from datetime import datetime, timedelta


rx = re.compile(r'''\[([\d:\- ]+)\] ERROR .*
^Traceback .*
[\s\S]+?
(?=^\[|\Z)''', re.M)

class TracebackExtractor(object):
    def __init__(self, log_file, duration=5*60):
        self.log_file = log_file
        self.duration = duration

    def __tail(self): 
        N = 1000
        stdin,stdout = os.popen2("tail -n %s %s"%(N, self.log_file))
        stdin.close()
        lines = stdout.readlines() 
        stdout.close()
        return "".join(lines)

    def extract(self):
        traceback_list = []
        content = self.__tail()
        for match in rx.finditer(content):
            traceback = match.group(0)
            log_time = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
            if log_time > datetime.now() - timedelta(seconds=self.duration):
                traceback_list.append(traceback)
        return traceback_list


class EmailSender(object):
    def __init__(self, host, port, email, password):
        self.email = email
        self.server = smtplib.SMTP_SSL(host, port)
        self.server.login(email, password)

    def send(self, to, subject, content, files=[]):
        msg = MIMEMultipart()
        msg['From'] = self.email 
        msg['To'] = to 
        msg['Subject'] = subject 
        body = content 
        msg.attach(MIMEText(body, 'plain'))

        for f in files:
            attachment = open(f, "rb")
            part = MIMEBase('application', 'octet-stream')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            filename = f.split("/")[-1]
            part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
            msg.attach(part)

        text = msg.as_string()
        self.server.sendmail(self.email, to, text)


if __name__ == "__main__":
    email_sender = EmailSender(**{
        "host": "",
        "port": "",
        "email": "",
        "password": "",
    })
    to = ""

    LOG_FILE = ""
    traceback_list = TracebackExtractor(LOG_FILE).extract()
    if len(traceback_list) > 0:
        subject = "EXCEPTION MONITOR"
        content = "\n\r\n\r".join(traceback_list)
        email_sender.send(to, subject, content)
        print "Send %s traceback to %s"%(len(traceback_list), to)
