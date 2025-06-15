# Summary

Basic tftp server created in python only implementing the RRQ functionality, and tries to implement [rfc 1350](https://datatracker.ietf.org/doc/html/rfc1350)

# Features
This program uses asyncio as its main runtime to ensure it is able to handle multiple requests **concurrently**(not in parallel). The main rationale fo that is that the main goal of a tftp server is to serve occasional traffic for the ever so uncommon file fetching operations instead of many devices relying on it. As such, intead of having to worry about maintaining correctness across the multiple processes, asyncio seems like the most suitable solution for the choice.

# How it works
When the tftp server `listen()` function is called (when start is called)
# Limitations
- currently the server only supports up to 65535 * 512 bytes file transfer ~ 33 MB file transfers due to no rollov er support
- currently there are no retries and timeut implemented