import smtplib

from email.mime.text import MIMEText

from email.mime.multipart import MIMEMultipart

from email.header import Header

from email.mime.application import MIMEApplication


class AttachmentEmailSender(object):

    def __init__(self):
        self.smtp_host = "smtp.office365.com"
        self.smtp_user = "bootroomchat_editor@outlook.com"
        self.smtp_pwd = "lirplwixqmmelukz"
        self.smtp_port = 587
        self.sender = "bootroomchat_editor@outlook.com"
        self._smtpSSLClient = smtplib.SMTP(self.smtp_host, self.smtp_port)
        self._smtpSSLClient.ehlo()  # Hostname to send for this command defaults to the fully qualified domain name of the local host.
        self._smtpSSLClient.starttls()  # Puts connection to SMTP server in TLS mode
        self._smtpSSLClient.ehlo()
        loginRes = self._smtpSSLClient.login(self.smtp_user, self.smtp_pwd)

        print("Login Result：loginRes=", loginRes)
        if loginRes and loginRes[0] == 235:
            print("Login successful，code = ", loginRes[0])
        else:
            print("Login failed，code=", loginRes[0])


    def send_email(self, tolist, subject, body, attachments):
        """
        :param tolist:
        :param subject:
        :param body:
        :param attachments:
        :return:
        """

        message = MIMEMultipart()
        message['Form'] = Header(self.sender)
        message['To'] = Header(";".join(tolist))
        message['Subject'] = Header(subject, 'utf-8')
        message.attach(MIMEText(body, 'plain', 'utf-8'))

        for path in attachments:
            name = path.split('/')[-1]
            att = MIMEApplication(open(path, 'rb').read())
            att['Content-Type'] = 'application/octet-stream'
            att.add_header('Content-Disposition', 'attachment', filename=name)
            message.attach(att)

        try:
            self._smtpSSLClient.sendmail(self.sender, tolist, message.as_string())
        except Exception as e:
            print("Email send failed，Exception：e=", e)



