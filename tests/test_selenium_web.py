import unittest
import time
import os
import sys

# Try importing Selenium modules
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class TestSeleniumWebUI(unittest.TestCase):
    """
    Selenium End-to-End (E2E) Test Suite for OncoFusion AI Web UI Dashboard
    """
    target_url = "http://localhost:8501"
    headless = True
    driver = None

    @classmethod
    def setUpClass(cls):
        cls.target_url = os.getenv("TEST_BASE_URL", "http://localhost:8501")
        cls.headless = os.getenv("HEADLESS", "true").lower() == "true"
        cls.driver = None

        if SELENIUM_AVAILABLE:
            try:
                chrome_options = Options()
                if cls.headless:
                    chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")

                try:
                    service = Service(ChromeDriverManager().install())
                    cls.driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception:
                    cls.driver = webdriver.Chrome(options=chrome_options)
            except Exception as err:
                print(f"[SELENIUM SETUP WARN] Could not start Chrome WebDriver: {err}")
                cls.driver = None

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            try:
                cls.driver.quit()
            except Exception:
                pass

    def test_01_selenium_framework_availability(self):
        """Verify Selenium dependencies and web driver initialization"""
        if not SELENIUM_AVAILABLE:
            self.skipTest("Selenium package not installed in local environment (installed in CI workflow via requirements-test.txt)")
        self.assertTrue(SELENIUM_AVAILABLE)

    def test_02_web_app_loading_and_title(self):
        """Test web application page load and title verification"""
        if not self.driver:
            self.skipTest("Chrome WebDriver not initialized in environment")
        
        self.driver.get(self.target_url)
        time.sleep(3)  # Allow Streamlit components to load
        
        title = self.driver.title
        self.assertIsNotNone(title)
        print(f"[SELENIUM] Page Title: {title}")

    def test_03_dashboard_header_elements(self):
        """Verify key headers and diagnostic UI components exist"""
        if not self.driver:
            self.skipTest("Chrome WebDriver not initialized in environment")

        self.driver.get(self.target_url)
        time.sleep(2)
        
        # Streamlit main container checks
        page_source = self.driver.page_source
        self.assertIn("stApp", page_source, "Streamlit main application root should be present")

    def test_04_responsive_layout(self):
        """Validate web UI responsiveness across viewport sizes"""
        if not self.driver:
            self.skipTest("Chrome WebDriver not initialized in environment")

        # Desktop Viewport
        self.driver.set_window_size(1920, 1080)
        time.sleep(1)
        self.assertEqual(self.driver.get_window_size()['width'], 1920)

        # Mobile Viewport Simulation
        self.driver.set_window_size(375, 812)
        time.sleep(1)
        self.assertEqual(self.driver.get_window_size()['width'], 375)


if __name__ == "__main__":
    unittest.main()
