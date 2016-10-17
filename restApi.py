#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

PORT_NUMBER = 54443

#This class will handles any incoming request from
#the browser
class myHandler(BaseHTTPRequestHandler):

        #Handler for the GET requests
        def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                # Send the html message
                self.wfile.write("Hello World !")
                return

        def do_POST(self):
                """Respond to a POST request."""
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write("<html><head><title>Title goes here.</title></head
                self.wfile.write("<body><p>This is a test.</p>")
                self.wfile.write("<body><form action='.' method='POST'><input type=
                # If someone went to "http://something.somewhere.net/foo/bar/",
                # then s.path equals "/foo/bar/".
                self.wfile.write("<p>POST: You accessed path: %s</p>" % s.path)
                self.wfile.write("</body></html>")
try:
        #Create a web server and define the handler to manage the
        #incoming request
        server = HTTPServer(('', PORT_NUMBER), myHandler)
        print 'Started httpserver on port ' , PORT_NUMBER

        #Wait forever for incoming htto requests
        server.serve_forever()

except KeyboardInterrupt:
        print '^C received, shutting down the web server'
        server.socket.close()

