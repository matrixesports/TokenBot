from Bot_Prod import runBotProd
from Bot_Staging import runBotStaging
import os
import http.server
import socketserver

ZEET_ENVIRONMENT = os.getenv('ZEET_ENVIRONMENT')
PORT = 8000

handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), handler) as httpd:
    print("Server started at localhost:" + str(PORT))
    httpd.serve_forever()
print(ZEET_ENVIRONMENT)





