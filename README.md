# Summary

Basic TFTP server created in Python only implementing the RRQ functionality, and tries to implement [RFC 1350](https://datatracker.ietf.org/doc/html/rfc1350).

# Features
This program uses asyncio as its main runtime to ensure it is able to handle multiple requests **concurrently** (not in parallel). The main rationale for that is that the main goal of a TFTP server is to serve occasional traffic for the ever so uncommon file-fetching operations instead of many devices relying on it. As such, instead of having to worry about maintaining correctness across the multiple processes, asyncio seems like the most suitable solution for the choice.
- Fetching files uses an LRU cache to reduce lookup times.
**Downside**: If the file is changed, unless it is not in the LRU cache, the file served would be the old version of the file.

# Testing
Run the `test_get.sh` in the `tests/` directory to perform end-to-end testing of the TFTP server. Make sure that your Python environment is activated before running the tests, as the tests will run the server automatically for you.

# Manual Testing

You can manually test the TFTP server using `curl` or the `tftp` command-line tool. Below are instructions for both methods.

## Testing with `curl`

The `curl` command supports TFTP and can be used to fetch files from the server.

### Fetching a File
To fetch a file from the TFTP server:
```bash
curl -o <output_file> tftp://<server_ip>/<filename>
```

#### Example:
```bash
curl -o config.ini tftp://127.0.0.1/config.ini
```
This command fetches the file `config.ini` from the TFTP server running on `127.0.0.1` and saves it locally as `config.ini`.

### Testing Concurrency
To test the server's ability to handle concurrent requests, you can use a loop to fetch the same file multiple times:
```bash
for i in {1..10}; do
  curl -o "config_$i.ini" tftp://127.0.0.1/config.ini &
done
wait
```
This command fetches the file `config.ini` 10 times concurrently and saves each copy as `config_1.ini`, `config_2.ini`, ..., `config_10.ini`.

---

## Testing with `tftp`

The `tftp` command-line tool is specifically designed for TFTP and can be used to interact with the server.

### Fetching a File
To fetch a file from the TFTP server:
1. Start the `tftp` client:
   ```bash
   tftp <server_ip>
   ```
2. Use the `get` command to fetch the file:
   ```bash
   get <filename>
   ```

#### Example:
```bash
tftp 127.0.0.1
get config.ini
```
This command fetches the file `config.ini` from the TFTP server running on `127.0.0.1`.

### Testing Concurrency
To test concurrency, you can run multiple `tftp` commands in parallel using a script:
```bash
for i in {1..10}; do
  echo -e "connect 127.0.0.1\nget config.ini\nquit" | tftp > "config_$i.ini" &
done
wait
```
This script fetches the file `config.ini` 10 times concurrently and saves each copy as `config_1.ini`, `config_2.ini`, ..., `config_10.ini`.

---

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

To run the server with custom settings:
```bash
python run.py --host 127.0.0.1 --port 8080 --max-block-size 1024 --timeout 5 --retries 2 --file-directory /path/to/files
```

### Explanation of Example:
- `--host 127.0.0.1`: The server will bind to the local machine's IP address.
- `--port 8080`: The server will listen on port 8080 instead of the default port 69.
- `--max-block-size 1024`: The maximum block size for file transfers is set to 1024 bytes.
- `--timeout 5`: The server will wait for 5 seconds for a client response before timing out.
- `--retries 2`: The server will retry failed transfers up to 2 times.
- `--file-directory /path/to/files`: Files will be served from the specified directory.

Ensure that the specified file directory exists and contains the files you want to serve.

---

# How it works
When the TFTP server `listen()` function is called (when `start()` is called), the server begins listening for incoming requests.

# Limitations
- Currently, only a basic implementation of RRQ is supported.
- [Option negotiation](https://datatracker.ietf.org/doc/html/rfc2347) is not supported (this server is pretty bare bones).