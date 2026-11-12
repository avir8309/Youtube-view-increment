from selenium import webdriver


def create_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")  # Disable GPU acceleration
    options.add_argument("--no-sandbox")  # Bypass OS security model
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    options.add_argument(
        "--proxy-server=http://127.0.0.1:8080"
    )

    driver = webdriver.Chrome(options=options)
    return driver


if __name__ == "__main__":
    driver = create_browser()

    try:
        driver.get("https://google.com")
        print("Title:", driver.title)

    finally:
        driver.quit()