# coding: utf-8

import base64
import sendgrid
from sendgrid.helpers.mail import (Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition)

def go_sendgrid(email_sender, email_recipients, subject, my_tenant, mail_txt, local_file, SENDGRID_API_KEY):
    
    # Send mail

	message = Mail(
		from_email=Email(email_sender),
		to_emails=email_recipients,
		subject="{} {}".format(subject, my_tenant),
		plain_text_content = Content("text/plain", mail_txt)
        )

	with open(local_file, 'rb') as f:
		data = f.read()
		f.close()
	
	encoded_file = base64.b64encode(data).decode()
	attachedFile = Attachment(
		FileContent(encoded_file),
		FileName(local_file),
		FileType('application/txt'),
		Disposition('attachment')
		)
	message.attachment = attachedFile

	try:
		sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
		response = sg.send(message)
		#print(response.status_code)
		#print(response.body)
		#print(response.headers)
	except Exception as e:
		print(e)
	finally:
		print("Email sent to:\n\t")
		for recipient in email_recipients:
			print(recipient[0])
			print()