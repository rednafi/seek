import pytest
import tempfile
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from scripts.sync import main


# Simple HTTP server to serve test data
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        content = b'{"key": "value"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


@pytest.fixture(scope="module")
def http_server():
    server = HTTPServer(("localhost", 8000), SimpleHTTPRequestHandler)
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield server
    server.shutdown()


async def test_main(http_server):
    api_url = "http://localhost:8000/"

    with tempfile.NamedTemporaryFile(suffix=".json") as temp_file:
        output_file = Path(temp_file.name)

        await main(api_url, output_file)

        assert output_file.exists()
        assert output_file.suffix == ".json"

        with output_file.open("r") as f:
            data = json.load(f)
            assert data == {"key": "value"}
