import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Add src to path so we can import pipeline
sys.path.append(os.path.join(os.path.dirname(__file__)))
from engine.core.pipeline import process_clip

PORT = int(os.environ.get('PORT', 8000))

class CaptionHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('web/index.html', 'rb') as f:
                self.wfile.write(f.read())
        elif self.path.startswith('/static/'):
            filepath = os.path.join('web', 'static', self.path[len('/static/'):])
            if os.path.exists(filepath):
                self.send_response(200)
                if filepath.endswith('.css'):
                    self.send_header('Content-type', 'text/css')
                elif filepath.endswith('.js'):
                    self.send_header('Content-type', 'application/javascript')
                self.end_headers()
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File not found")
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        if self.path == '/generate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                video_url = data.get('video_url')
                styles = data.get('styles', ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"])
                
                if not video_url:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Missing video_url")
                    return
                
                captions = process_clip(video_url, styles, "web-test-task")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'captions': captions}).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_error(404, "Not found")

if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    server = HTTPServer(('', PORT), CaptionHandler)
    print(f"Starting testing server on http://localhost:{PORT}")
    server.serve_forever()
