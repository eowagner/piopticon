import smtplib

gmail_user = '' 
gmail_password = ''

sent_from = gmail_user  
to = ['e.o.wagner@gmail.com']  
subject = 'OMG Super Important Message'  
body = 'Hey, what\'s up?\n\n- You'

email_text = """\  
From: %s  
To: %s  
Subject: %s

%s
""" % (sent_from, ", ".join(to), subject, body)

try:  
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(gmail_user, gmail_password)
    server.sendmail(sent_from, to, email_text)
    server.close()

    print('Email sent!')
except:  
    print('Something went wrong...')