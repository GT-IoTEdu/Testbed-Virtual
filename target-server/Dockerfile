FROM nginx:alpine

# Instala ferramentas adicionais para SSH e FTP (alvos de outros ataques)
RUN apk add --no-cache openssh vsftpd bash

# Configura SSH
RUN ssh-keygen -A && \
    echo 'root:password123' | chpasswd && \
    echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config && \
    echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config

# Configura página web de teste
RUN echo '<html><body><h1>SIMIR Target Server</h1><p>This is a vulnerable test server for attack simulation</p></body></html>' > /usr/share/nginx/html/index.html

# Cria página de login fake
RUN echo '<html><body><h1>Login</h1><form method="POST" action="/login"><input name="user" placeholder="Username"><input name="pass" type="password" placeholder="Password"><button>Login</button></form></body></html>' > /usr/share/nginx/html/login.html

# Script de inicialização
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80 22 21

ENTRYPOINT ["/entrypoint.sh"]
