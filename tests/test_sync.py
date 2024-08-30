import json
import tempfile
import threading
from collections.abc import Iterator
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Iterator

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
    with ExitStack() as stack:
        server = HTTPServer(("localhost", 8000), SimpleHTTPRequestHandler)
        server_ready = threading.Event()

        def start_server():
            server_ready.set()
            server.serve_forever()

        thread = stack.enter_context(threading.Thread(target=start_server, daemon=True))
        thread.start()

        server_ready.wait()  # Ensure the server is fully started before yielding

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
