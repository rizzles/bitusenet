import smtplib
import email
import logging


def connect_gmail():
    mailconn = None
    try:
        mailconn = smtplib.SMTP('smtp.gmail.com', 587)
        mailconn.starttls()
    except:
        logging.error('Count not connect to gmail servers')
        return False

    try:
        mailconn.login('support@bitusenet.com', 'Ie2kAdji9Nwi8')
    except:
        logging.error('Password for gmail servers was incorrect')
        return False

    return mailconn


def send_user_password(emailaddress, link):
    logging.info('Reset email being sent for %s'% emailaddress)
    mailconn = connect_gmail()
    if not mailconn:
        return False

    msg = email.MIMEMultipart.MIMEMultipart('related')
    msg['From'] = 'Bitusenet Support'
    msg['To'] = emailaddress
    msg['Subject'] = 'Bitusenet Password Reset Instructions'

    alternative = email.MIMEMultipart.MIMEMultipart('alternative')
    msg.attach(alternative)

    text = email.MIMEText.MIMEText("<img src='cid:image1'><br>We've sent this message because someone requested a new password for a bitusenet account.<br>Follow this link to reset your password. <p><a href='http\
://www.bitusenet.com/passwordreset?id=%s'>http://www.bitusenet.com/passwordreset?id=%s</a><p>Thank You,<br>support@bitusenet.com"% (link, link), "html")
    alternative.attach(text)

    fp = open('/home/ubuntu/bitusenet/static/images/logomedium.png', 'rb')
    msgimage = email.MIMEImage.MIMEImage(fp.read())
    fp.close()

    msgimage.add_header('Content-ID', '<image1>')
    msg.attach(msgimage)

    mailconn.sendmail('support@bitusenet.com', emailaddress, msg.as_string())

    try: 
        mailconn.close()
    except:
        logging.warning('Error trying to close email server connection')
