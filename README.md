# Summary

Basic tftp server created in python only implementing the RRQ functionality, and tries to implement [rfc 1350](https://datatracker.ietf.org/doc/html/rfc1350)

# Features
This program uses asyncio as its main runtime to ensure it is able to handle multiple requests **concurrently**(not in parallel). The main rationale fo that is that the main goal of a tftp server is to serve occasional traffic for the ever so uncommon file fetching operations instead of many devices relying on it. As such, intead of having to worry about maintaining correctness across the multiple processes, asyncio seems like the most suitable solution for the choice.
- fetching files uses an lru cache to reduce lookup times.
**Downside**: if the file is changed, unless it is not in the lru cache, the file served would be the old version of the file

# Testing
run the test_get.sh in the `tests/` directoryto perform e2e testing of the tftp server. Make sure that your python environment is activated before running the tests, as the tests will run the server automatically for you

# Custom Configuration

You can specify custom configuration options using command-line arguments when running the TFTP server.

## Command-Line Arguments
The following options are available:

- `--host`: Host to bind the TFTP server (default: `0.0.0.0`).
- `--port`: Port to bind the TFTP server (default: `69`).
- `--max-block-size`: Maximum block size for file transfers (default: `512`).
- `--timeout`: Timeout in seconds for client responses (default: `1`).
- `--retries`: Number of retries for failed transfers (default: `3`).
- `--file-directory`: Directory to serve files from (default: `/tmp/tftp`).

## Example Usage
To run the server with default settings:
```bash
python run.py
```

# How it works
When the tftp server `listen()` function is called (when start is called)
# Limitations
- currently a basic implementation of rrq is implemented
- [option negatiation](https://datatracker.ietf.org/doc/html/rfc2347) is not supported (this server is pretty bare bones)