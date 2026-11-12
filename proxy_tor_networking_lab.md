# Proxy + Tor Networking Lab

## Purpose

This guide demonstrates how to route **authorized connectivity tests**
through a local HTTP proxy or Tor SOCKS5 endpoint. It is intended for
learning proxy protocols, diagnosing connectivity, and testing services
you own or have permission to test.

It does **not** cover hiding automated activity, bypassing CAPTCHAs,
evading rate limits, rotating identities to avoid detection, or
manufacturing engagement.

## 1. Architecture

``` text
Python test client
      |
      | HTTP(S) request
      v
Local proxy endpoint
  - Squid: 127.0.0.1:3128
  - Tor SOCKS5: 127.0.0.1:9050
      |
      v
Destination service
```

With Tor, the Tor client manages its circuits. Applications connect to
the local SOCKS5 listener; they do not select individual Tor relays
themselves.

## 2. Prerequisites

-   Python 3
-   A running Squid proxy, if testing HTTP proxy forwarding
-   A locally running Tor service with a SOCKS listener, if testing Tor
-   Permission to test the destination service
-   A conservative request rate and clear test identification

Install Requests with SOCKS support:

``` bash
python -m pip install "requests[socks]"
```

## 3. Test a single Google connectivity request through Tor

Make one request and inspect the HTTP status and response metadata:

``` python
import requests
import time

TOR_PROXY = "socks5h://127.0.0.1:9050"

proxies = {
    "http": TOR_PROXY,
    "https": TOR_PROXY,
}

started = time.perf_counter()

response = requests.get(
    "https://www.google.com/",
    proxies=proxies,
    timeout=30,
    headers={"User-Agent": "ProxyNetworkingLab/1.0"},
)

elapsed_ms = (time.perf_counter() - started) * 1000

print("HTTP status:", response.status_code)
print("Final URL:", response.url)
print("Elapsed ms:", round(elapsed_ms, 2))
print("Content bytes:", len(response.content))
```

`socks5h://` (without the space) asks the SOCKS proxy to resolve the
hostname, rather than resolving it locally first.

Google may return a redirect, CAPTCHA, access restriction, or other
response. Do not attempt to bypass those controls. Stop testing if the
service blocks or challenges the requests.

## 4. Verify that the Tor SOCKS listener is available

On Windows PowerShell:

``` powershell
Test-NetConnection 127.0.0.1 -Port 9050
```

A successful TCP connection should report:

``` text
TcpTestSucceeded : True
```

The port must match the SOCKS listener configured in your Tor
installation. Some Tor Browser configurations use port `9150` instead.

## 5. Understand the SOCKS5 exchange

A SOCKS5 client typically performs these steps:

1.  **Greeting:** sends SOCKS version and supported authentication
    methods.
2.  **Method selection:** the proxy selects one supported method.
3.  **Authentication:** performed only if the selected method requires
    it.
4.  **CONNECT request:** asks the proxy to connect to a destination host
    and port.
5.  **Reply:** the proxy reports success or a failure code.
6.  **Data exchange:** application traffic passes through the
    established connection.

For a typical local Tor SOCKS listener, no username/password
authentication is configured by default. Follow the configuration of
your own Tor service.

## 6. Repeated connectivity tests: safe practice

For a service you own or are explicitly authorized to test:

-   Prefer a staging endpoint or local test server.
-   Set a low, documented request rate.
-   Use a descriptive User-Agent identifying your test client.
-   Add timeouts and stop on `429`, `403`, CAPTCHA, or other
    access-control responses.
-   Respect the service's published terms, robots guidance where
    applicable, and rate limits.
-   Log timestamps, status codes, latency, and errors.
-   Do not rotate Tor circuits or proxy identities to get around blocks
    or request limits.

Example: a deliberately slow test against an endpoint you control:

``` python
import time
import requests

TARGET = "https://your-authorized-test-host.example/health"

for attempt in range(3):
    try:
        response = requests.get(
            TARGET,
            timeout=10,
            headers={"User-Agent": "AuthorizedNetworkLab/1.0"},
        )
        print(attempt + 1, response.status_code, response.elapsed.total_seconds())

        if response.status_code in (403, 429):
            print("Access restriction or rate limit received; stopping.")
            break

    except requests.RequestException as exc:
        print("Request failed:", exc)
        break

    time.sleep(10)
```

Replace the example hostname with a service you own or have permission
to test. This example intentionally uses a fixed, slow interval and
stops when access is restricted.

## 7. Troubleshooting

  -----------------------------------------------------------------------
  Symptom                             What to check
  ----------------------------------- -----------------------------------
  Connection refused on port 9050     Tor is running and the SOCKS
                                      listener uses that port

  SOCKS connection error              `requests[socks]` is installed and
                                      the proxy URL is correct

  Timeout                             Tor circuit readiness, network
                                      connectivity, and destination
                                      availability

  HTTP 403 or 429                     The destination denied or
                                      rate-limited the request; stop and
                                      follow its rules

  Google CAPTCHA                      Google is challenging the request;
                                      do not attempt to evade it
  -----------------------------------------------------------------------

## 8. Key distinction

A proxy changes the network path used by a request. Tor routes traffic
through a Tor circuit. Neither makes automated requests undetectable,
guarantees access, or grants permission to bypass a website's controls.
