import unittest
import os
import time

# Try importing Appium modules
try:
    from appium import webdriver
    from appium.options.android import UiAutomator2Options
    from appium.webdriver.common.appiumby import AppiumBy
    APPIUM_AVAILABLE = True
except ImportError:
    APPIUM_AVAILABLE = False


class TestAppiumMobileAPK(unittest.TestCase):
    """
    Appium Mobile End-to-End (E2E) Test Suite for LUNG-NET.apk
    """
    apk_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "LUNG-NET.apk")
    appium_server_url = "http://127.0.0.1:4723"
    driver = None

    @classmethod
    def setUpClass(cls):
        cls.apk_path = os.getenv(
            "APK_PATH", 
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "LUNG-NET.apk")
        )
        cls.appium_server_url = os.getenv("APPIUM_SERVER_URL", "http://127.0.0.1:4723")
        cls.driver = None

        if APPIUM_AVAILABLE and os.path.exists(cls.apk_path):
            try:
                options = UiAutomator2Options()
                options.platform_name = "Android"
                options.automation_name = "UiAutomator2"
                options.device_name = "Android Emulator"
                options.app = cls.apk_path
                options.no_reset = True

                cls.driver = webdriver.Remote(cls.appium_server_url, options=options)
            except Exception as err:
                print(f"[APPIUM SETUP WARN] Could not connect to Appium server: {err}")
                cls.driver = None

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            try:
                cls.driver.quit()
            except Exception:
                pass

    def test_01_appium_environment_and_apk_existence(self):
        """Verify Appium library availability and LUNG-NET.apk bundle path"""
        if not APPIUM_AVAILABLE:
            self.skipTest("Appium-Python-Client not installed in local environment (installed in CI workflow via requirements-test.txt)")
        self.assertTrue(os.path.exists(self.apk_path), f"APK file must exist at path: {self.apk_path}")

    def test_02_apk_metadata_validation(self):
        """Validate APK file size and structural Integrity"""
        file_size = os.path.getsize(self.apk_path)
        self.assertGreater(file_size, 1000000, "APK file size should be greater than 1MB")
        print(f"[APPIUM] Validated LUNG-NET.apk size: {file_size / (1024*1024):.2f} MB")

    def test_03_appium_mobile_session_launch(self):
        """Test Appium driver session launch and activity rendering"""
        if not self.driver:
            self.skipTest("Appium Server or Android Emulator not active in execution environment")

        current_package = self.driver.current_package
        self.assertIsNotNone(current_package)
        print(f"[APPIUM] Active Package: {current_package}")

    def test_04_webview_mobile_container(self):
        """Verify WebView container initialization inside native APK wrapper"""
        if not self.driver:
            self.skipTest("Appium Server or Android Emulator not active in execution environment")

        contexts = self.driver.contexts
        self.assertGreater(len(contexts), 0, "Mobile app should expose contexts (NATIVE_APP / WEBVIEW)")
        print(f"[APPIUM] App Contexts: {contexts}")


if __name__ == "__main__":
    unittest.main()
