"""Run a bounded authorized connectivity test through Tor."""

import logging
import os
import time

import requests


TOR_PROXY = "socks5h://127.0.0.1:9050"
TARGET = "https://www.youtube.com/live/OOkcb7V-MnI?si=1Pcp90m40Oxdqy2A"
RUN_DURATION_SECONDS = 30 * 60
REQUEST_INTERVAL_SECONDS = 10
TIMEOUT_SECONDS = 30
USER_AGENT = "ProxyNetworkingLab/1.0"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logger = logging.getLogger(__name__)


def main() -> None:
    if not TARGET:
        logger.error(
            "AUTHORIZED_TARGET is not set. Refusing to send repeated requests "
            "without an explicit authorized test URL."
        )
        raise SystemExit(2)

    logger.info("Starting authorized proxy connectivity test")
    logger.info("Target URL: %s", TARGET)
    logger.info("Proxy type: Tor SOCKS5 with remote DNS resolution")
    logger.info("Proxy endpoint: %s", TOR_PROXY)
    logger.info("Request timeout: %s seconds", TIMEOUT_SECONDS)
    logger.info("Maximum run duration: %s seconds", RUN_DURATION_SECONDS)
    logger.info("Interval between requests: %s seconds", REQUEST_INTERVAL_SECONDS)
    logger.info("User-Agent: %s", USER_AGENT)

    proxies = {
        "http": TOR_PROXY,
        "https": TOR_PROXY,
    }

    logger.info("Configured proxy schemes: %s", ", ".join(sorted(proxies)))
    deadline = time.monotonic() + RUN_DURATION_SECONDS
    attempt = 0

    while time.monotonic() < deadline:
        attempt += 1
        logger.info("Starting request %d", attempt)
        started = time.perf_counter()

        try:
            response = requests.get(
                TARGET,
                proxies=proxies,
                timeout=TIMEOUT_SECONDS,
                headers={"User-Agent": USER_AGENT},
            )
        except requests.RequestException as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.error("Request %d failed after %.2f ms", attempt, elapsed_ms)
            logger.error("Failure type: %s", type(exc).__name__)
            logger.error("Failure details: %s", exc)
            break

        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "Request %d completed: status=%s url=%s elapsed_ms=%.2f "
            "content_bytes=%s headers=%s",
            attempt,
            response.status_code,
            response.url,
            elapsed_ms,
            len(response.content),
            len(response.headers),
        )

        if response.status_code in (403, 429):
            logger.warning(
                "Access restriction or rate limit received (%s); stopping.",
                response.status_code,
            )
            break

        content_preview = response.text[:200].lower()
        if "captcha" in content_preview or "verify you are human" in content_preview:
            logger.warning("Challenge/CAPTCHA indicator received; stopping.")
            break

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        sleep_for = min(REQUEST_INTERVAL_SECONDS, remaining)
        logger.info("Waiting %.2f seconds before the next request", sleep_for)
        time.sleep(sleep_for)

    logger.info("Test run finished after %d request(s)", attempt)


if __name__ == "__main__":
    main()
