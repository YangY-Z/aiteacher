#!/usr/bin/env python3
"""End-to-end test for improvement module."""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright, expect

# Add backend to path for with_server
sys.path.insert(0, str(Path(__file__).parent / "ai-teacher-backend"))
from tests.with_server import with_server


async def test_improvement_flow():
    """Test the complete improvement flow."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Navigate to login
            await page.goto("http://localhost:5173/login")
            await page.wait_for_load_state("networkidle")

            # Login with test account
            await page.fill('input[placeholder="请输入手机号"]', "13800138001")
            await page.fill('input[type="password"]', "test123")
            await page.click('button:has-text("登录")')
            await page.wait_for_url("**/learn", timeout=5000)
            print("✓ Login successful")

            # Navigate to improvement module
            await page.click('button:has-text("专项提升")')
            await page.wait_for_url("**/improvement", timeout=5000)
            print("✓ Navigated to improvement page")

            # Fill score upload form
            await page.fill('input[placeholder="例如：期中考试"]', "期中考试")
            await page.fill('input[placeholder="请输入得分"]', "65")
            await page.fill('input[placeholder="请输入总分"]', "100")
            await page.fill('textarea[placeholder="例如：图象题错了2道，解析式求解不熟练"]', "图象题错了2道")
            await page.fill('input[placeholder="请输入可用时间"]', "40")
            await page.click('text=开始诊断')
            print("✓ Submitted score form")

            # Wait for diagnosis or clarification
            await page.wait_for_selector('text=诊断结果', timeout=10000)
            print("✓ Diagnosis completed")

            # Generate plan
            await page.click('button:has-text("生成学习方案")')
            await page.wait_for_selector('text=学习方案', timeout=10000)
            print("✓ Plan generated")

            # Start first step
            await page.click('button:has-text("开始学习")')
            await page.wait_for_timeout(2000)
            print("✓ Started first learning step")

            # Complete first step
            await page.click('button:has-text("完成本步")')
            await page.wait_for_timeout(2000)
            print("✓ Completed first step")

            # Take quiz
            await page.click('button:has-text("开始小测")')
            await page.wait_for_selector('text=专项提升小测', timeout=5000)
            print("✓ Quiz loaded")

            # Submit quiz (select first option for all questions)
            questions = await page.query_selector_all('.ant-radio-group')
            for i, question in enumerate(questions):
                first_option = await question.query_selector('.ant-radio-wrapper')
                if first_option:
                    await first_option.click()

            await page.click('button:has-text("提交答案")')
            await page.wait_for_selector('text=测试结果', timeout=5000)
            print("✓ Quiz submitted")

            print("\n✅ All tests passed!")

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            await page.screenshot(path="test_failure.png")
            raise
        finally:
            await browser.close()


async def main():
    """Run test with servers."""
    backend_dir = Path(__file__).parent / "ai-teacher-backend"
    frontend_dir = Path(__file__).parent / "ai-teacher-frontend"

    backend_cmd = f"cd {backend_dir} && venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8008"
    frontend_cmd = f"cd {frontend_dir} && npm run dev"

    async with with_server(backend_cmd, port=8008, startup_time=3):
        async with with_server(frontend_cmd, port=5173, startup_time=5):
            await test_improvement_flow()


if __name__ == "__main__":
    asyncio.run(main())
