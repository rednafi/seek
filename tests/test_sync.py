import json
import socket
import tempfile
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Event, Thread

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
    server_ready = Event()

    def start_server() -> None:
        server_ready.set()
        server.serve_forever()

    thread = Thread(target=start_server, daemon=True)
    thread.start()

    server_ready.wait()

    # Ensure the server is ready by attempting a connection
    with socket.create_connection(("localhost", 8000), timeout=5):
        pass

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
