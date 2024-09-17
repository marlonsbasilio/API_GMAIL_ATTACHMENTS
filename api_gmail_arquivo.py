import base64
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Defina os escopos necessários
SCOPES = ['https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.appdata',
        'https://www.googleapis.com/auth/drive.file',
        'https://mail.google.com/',
        'https://www.googleapis.com/auth/gmail.send']

def authenticate():
    """Autentica com o Google OAuth 2.0"""
    creds = None
    token_path = 'token.json'
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # Se não houver credenciais válidas disponíveis, solicite que o usuário faça login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            flow.redirect_uri = 'http://localhost:8080/'
            # flow.authorization_url(prompt='consent', access_type='offline')
            creds = flow.run_local_server(port = 8080, prompt='consent', access_type='offline')
        # Salve os tokens de acesso para uso posterior

        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    return creds

def create_message_with_attachment(sender, to, subject, message_text, file_path):
    """Cria uma mensagem para um e-mail com um anexo."""
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    # Adiciona o corpo da mensagem
    msg = MIMEText(message_text)
    message.attach(msg)

    # Adiciona o anexo
    attachment = MIMEBase('application', 'octet-stream')
    with open(file_path, 'rb') as file:
        attachment.set_payload(file.read())
    encoders.encode_base64(attachment)
    attachment.add_header(
        'Content-Disposition',
        f'attachment; filename= {os.path.basename(file_path)}'
    )
    message.attach(attachment)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message, 'to': to, 'subject': subject}

def send_message(service, user_id, message):
    """Envia uma mensagem de e-mail e retorna metadados sobre a operação."""
    try:
        sent_message = service.users().messages().send(userId=user_id, body=message).execute()
        metadata = {
            'success': True,
            'message_id': sent_message['id'],
            'to': message['to'],
            'subject': message['subject']
        }
    except Exception as error:
        metadata = {
            'success': False,
            'error': str(error),
            'to': message['to'],
            'subject': message['subject']
        }
    return metadata

def main():
    # Verifique o diretório de trabalho atual
    # print("Current working directory:", os.getcwd())

    # Autentica e configura a API do Gmail
    creds = authenticate()
    service = build('gmail', 'v1', credentials=creds)

    # Define o conteúdo do e-mail e o anexo
    sender = 'marlonsbasilio@gmail.com'  # Substitua pelo seu e-mail
    to = 'marlonsbasilio@gmail.com'  # Substitua pelo e-mail do destinatário
    subject = 'Testando mensagem com arquivo PDF'
    message_text = 'Testando mensagem com arquivo'
    file_path = 'ML_Art_Marlon.pdf'  # Substitua pelo caminho do seu arquivo de anexo

    # Cria a mensagem com anexo
    message = create_message_with_attachment(sender, to, subject, message_text, file_path)

    # Envia a mensagem e obtém os metadados
    email_metadata = send_message(service, 'me', message)

    # Exibe os metadados
    print(email_metadata)

if __name__ == '__main__':
    main()
