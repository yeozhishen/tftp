# Summary

Basic tftp server created in python only implementing the RRQ functionality, and tries to implement [rfc 1350](https://datatracker.ietf.org/doc/html/rfc1350)

# Features
This program uses asyncio as its main runtime to ensure it is able to handle multiple requests **concurrently**(not in parallel). The main rationale fo that is that the main goal of a tftp server is to serve occasional traffic for the ever so uncommon file fetching operations instead of many devices relying on it. As such, intead of having to worry about maintaining correctness across the multiple processes, asyncio seems like the most suitable solution for the choice.
- fetching files uses an lru cache to reduce lookup times.
**Downside**: if the file is changed, unless it is not in the lru cache, the file served would be the old version of the file

# Testing
run the test_get.sh in the `tests/` directoryto perform e2e testing of the tftp server. Make sure that your python environment is activated before running the tests, as the tests will run the server automatically for you

# How it works
When the tftp server `listen()` function is called (when start is called)
# Limitations
- currently a basic implementation of rrq is implemented