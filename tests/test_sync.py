import json
import tempfile
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

import pytest

from scripts.sync import main


# Simple HTTP server to serve test data
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        content = b'{"key": "value"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


@pytest.fixture(scope="module")
def http_server() -> Iterator[HTTPServer]:
    server = HTTPServer(("localhost", 8000), SimpleHTTPRequestHandler)
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield server
    server.shutdown()


async def test_main(http_server) -> None:
    api_url = "http://localhost:8000/"

    with tempfile.NamedTemporaryFile(suffix=".json") as temp_file:
        output_file = Path(temp_file.name)

        await main(api_url, output_file)

        assert output_file.exists()
        assert output_file.suffix == ".json"

        with output_file.open("r") as f:
            data = json.load(f)
            assert data == {"key": "value"}
