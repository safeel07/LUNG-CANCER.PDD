import sys
import os
import unittest
import json
import time
from datetime import datetime

# Enforce project root in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test classes
from tests.test_selenium_web import TestSeleniumWebUI
from tests.test_appium_mobile import TestAppiumMobileAPK



def run_test_suite_and_generate_report():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "test-reports")
    os.makedirs(output_dir, exist_ok=True)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestSeleniumWebUI))
    suite.addTest(loader.loadTestsFromTestCase(TestAppiumMobileAPK))

    print("==================================================================")
    print("    EXECUTING ONCOFUSION AI E2E TEST SUITE (SELENIUM + APPIUM)   ")
    print("==================================================================")

    results_details = []
    total_passed = 0
    total_failed = 0
    total_skipped = 0

    start_timestamp = datetime.now().isoformat()
    start_time = time.time()

    def _flatten(suite_or_case):
        tests = []
        if isinstance(suite_or_case, unittest.TestSuite):
            for sub in suite_or_case:
                tests.extend(_flatten(sub))
        elif isinstance(suite_or_case, unittest.TestCase):
            tests.append(suite_or_case)
        return tests

    all_tests = _flatten(suite)

    for test_case in all_tests:
        test_name = test_case.id()
        category = "Selenium Web" if "TestSeleniumWebUI" in test_name else "Appium Mobile"
        method_name = test_name.split('.')[-1]

        result = unittest.TestResult()
        t0 = time.time()
        test_case.run(result)
        duration = round(time.time() - t0, 4)

        if result.wasSuccessful() and len(result.skipped) == 0:
            status = "PASSED"
            total_passed += 1
            reason = "Test executed successfully."
        elif len(result.skipped) > 0:
            status = "SKIPPED"
            total_skipped += 1
            reason = result.skipped[0][1]
        else:
            status = "FAILED"
            total_failed += 1
            err_msg = result.errors[0][1] if result.errors else (result.failures[0][1] if result.failures else "Unknown error")
            reason = err_msg.splitlines()[-1] if err_msg else "Failure detected."

        print(f"[{category:<15}] {method_name:<45} : {status} ({duration}s)")

        results_details.append({
            "test_name": method_name,
            "full_id": test_name,
            "category": category,
            "status": status,
            "duration_seconds": duration,
            "details": reason
        })

    elapsed_total = round(time.time() - start_time, 2)
    total_tests = len(results_details)

    # 1. Save JSON Report
    json_report = {
        "title": "OncoFusion AI Selenium & Appium Automated Test Execution Report",
        "timestamp": start_timestamp,
        "duration_seconds": elapsed_total,
        "summary": {
            "total": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "pass_rate": f"{(total_passed / total_tests * 100):.1f}%" if total_tests > 0 else "0%"
        },
        "tests": results_details
    }

    json_path = os.path.join(output_dir, "report.json")
    with open(json_path, "w") as f:
        json.dump(json_report, f, indent=2)

    # 2. Save JUnit XML Report
    xml_path = os.path.join(output_dir, "junit.xml")
    with open(xml_path, "w") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(f'<testsuite name="OncoFusion-AI-E2E-Suite" tests="{total_tests}" failures="{total_failed}" skipped="{total_skipped}" time="{elapsed_total}">\n')
        for item in results_details:
            f.write(f'  <testcase classname="{item["category"]}" name="{item["test_name"]}" time="{item["duration_seconds"]}">\n')
            if item["status"] == "SKIPPED":
                f.write(f'    <skipped message="{item["details"]}"/>\n')
            elif item["status"] == "FAILED":
                f.write(f'    <failure message="{item["details"]}"/>\n')
            f.write(f'  </testcase>\n')
        f.write(f'</testsuite>\n')

    # 3. Save Interactive HTML Report
    html_content = generate_html_report(json_report)
    html_path = os.path.join(output_dir, "index.html")
    with open(html_path, "w") as f:
        f.write(html_content)

    print("-" * 66)
    print(f"Summary: {total_tests} Tests | {total_passed} Passed | {total_failed} Failed | {total_skipped} Skipped")
    print(f"Reports successfully generated at:\n  - HTML : {html_path}\n  - JSON : {json_path}\n  - XML  : {xml_path}")
    print("=" * 66)

    return 0 if total_failed == 0 else 1


def generate_html_report(data):
    summary = data["summary"]
    rows = ""
    for t in data["tests"]:
        badge_class = "badge-success" if t["status"] == "PASSED" else ("badge-warning" if t["status"] == "SKIPPED" else "badge-danger")
        rows += f"""
        <tr>
            <td><strong>{t["category"]}</strong></td>
            <td><code>{t["test_name"]}</code></td>
            <td><span class="badge {badge_class}">{t["status"]}</span></td>
            <td>{t["duration_seconds"]}s</td>
            <td class="text-muted">{t["details"]}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data["title"]}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #0f172a; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; }}
        .card {{ background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; }}
        .table {{ color: #cbd5e1; vertical-align: middle; }}
        .table-dark {{ --bs-table-bg: #1e293b; }}
        .badge-success {{ background-color: #059669; color: #ffffff; padding: 6px 12px; border-radius: 6px; }}
        .badge-warning {{ background-color: #d97706; color: #ffffff; padding: 6px 12px; border-radius: 6px; }}
        .badge-danger {{ background-color: #dc2626; color: #ffffff; padding: 6px 12px; border-radius: 6px; }}
        .stat-card {{ padding: 20px; text-align: center; border-radius: 10px; background: #090d16; border: 1px solid #1e293b; }}
        .stat-num {{ font-size: 2.2rem; font-weight: 700; margin-bottom: 0; }}
        .stat-label {{ color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; }}
    </style>
</head>
<body class="py-4">
    <div class="container">
        <div class="card p-4 mb-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div>
                    <h2 class="fw-bold mb-1" style="color: #38bdf8;">🧪 OncoFusion AI E2E Automation Report</h2>
                    <p class="text-secondary mb-0">Selenium Web UI & Appium Mobile Test Pipeline Execution</p>
                </div>
                <div class="text-end">
                    <span class="badge bg-primary fs-6">{data["timestamp"]}</span>
                </div>
            </div>
            
            <div class="row g-3 my-2">
                <div class="col-md-2">
                    <div class="stat-card">
                        <p class="stat-num text-info">{summary["total"]}</p>
                        <p class="stat-label">Total Tests</p>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="stat-card">
                        <p class="stat-num text-success">{summary["passed"]}</p>
                        <p class="stat-label">Passed</p>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="stat-card">
                        <p class="stat-num text-warning">{summary["skipped"]}</p>
                        <p class="stat-label">Skipped</p>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="stat-card">
                        <p class="stat-num text-danger">{summary["failed"]}</p>
                        <p class="stat-label">Failed</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <p class="stat-num text-warning">{summary["pass_rate"]}</p>
                        <p class="stat-label">Pass Rate ({data["duration_seconds"]}s)</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="card p-4">
            <h4 class="mb-3 fw-bold" style="color: #94a3b8;">Detailed Test Case Execution Breakdown</h4>
            <div class="table-responsive">
                <table class="table table-dark table-hover align-middle">
                    <thead>
                        <tr style="border-bottom: 2px solid #334155;">
                            <th>Framework</th>
                            <th>Test Method</th>
                            <th>Status</th>
                            <th>Duration</th>
                            <th>Execution Log / Notes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(run_test_suite_and_generate_report())
