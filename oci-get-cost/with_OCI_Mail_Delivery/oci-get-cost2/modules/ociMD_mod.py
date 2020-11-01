# coding: utf-8

import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def go_ociMD(email_sender, email_recipients, subject, body, local_file, smtp_user, smtp_password, smtp_server, smtp_port, my_tenant):

	# Create a multipart message and set headers
	message = MIMEMultipart()
	message["From"] = email_sender
	message["To"] = email_recipients
	message["Subject"] = "{} {}".format(subject, my_tenant)
	#message["Bcc"] = receiver_email

	# Add body to email
	message.attach(MIMEText(body, "plain"))

	# Open local_file in binary mode
	with open(local_file, "rb") as attachment:
		# Add file as application/octet-stream
		part = MIMEBase("application", "octet-stream")
		part.set_payload(attachment.read())

	# Encode file in ASCII characters to send by email    
	encoders.encode_base64(part)

	# Add header as key/value pair to attachment part
	part.add_header(
		"Content-Disposition",
		f"attachment; filename= {local_file}",
	)

	# Add attachment to message and convert message to string
	message.attach(part)
	text = message.as_string()

	# Log in to server using secure context and send email
	context = ssl.create_default_context()
	try:
		server = smtplib.SMTP(smtp_server,smtp_port)
		server.ehlo()
		server.starttls(context=context) # Secure the connection
		server.ehlo()	
		server.login(smtp_user, smtp_password)
		server.sendmail(email_sender, email_recipients, text)

	except Exception as e:
		# Print any error messages to stdout
		print(e)
	finally:
		server.quit()