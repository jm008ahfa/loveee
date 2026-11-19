import os
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(os.environ["TEMP"]) / "loveee_shots"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8000"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SLUG = "to-my-love-yz5hwzzxri12"
LOCKED = "to-my-love-lry1qaum5day"
DRAFT = "to-my-love-k6y85hbeg7gv"


def shot(page, name, full=False, wait=900):
    page.wait_for_timeout(wait)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("shot", name)


def warm_scroll(page):
    """Trigger scroll-based reveal animations before a full-page capture."""
    page.evaluate(
        """() => new Promise(resolve => {
            const step = Math.round(window.innerHeight * 0.7);
            let y = 0;
            const timer = setInterval(() => {
                y += step;
                window.scrollTo(0, y);
                if (y >= document.body.scrollHeight) {
                    clearInterval(timer);
                    window.scrollTo(0, 0);
                    setTimeout(resolve, 400);
                }
            }, 120);
        })"""
    )


def open_letter(page):
    # Playwright's locator actionability is unreliable on this page in headless
    # Chrome (GSAP + CSS animations), but the click handler itself is fine.
    page.evaluate("document.querySelector('#openLetter').click()")


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME, headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 960}, device_scale_factor=1)
    page = ctx.new_page()

    page.goto(BASE + "/", wait_until="networkidle")
    shot(page, "01_home_hero")
    warm_scroll(page)
    shot(page, "02_home_full", full=True, wait=600)

    page.goto(BASE + "/explore/", wait_until="networkidle")
    warm_scroll(page)
    shot(page, "03_explore", full=True, wait=600)

    page.goto(BASE + "/accounts/login/", wait_until="networkidle")
    shot(page, "04_login")

    page.fill("#id_username", "demo")
    page.fill("#id_password", "LoveLetter2026!")
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    warm_scroll(page)
    shot(page, "05_dashboard", full=True, wait=800)

    page.evaluate("document.querySelector('[data-qr]').click()")
    shot(page, "05b_dashboard_qr", wait=700)
    page.evaluate("document.querySelector('[data-modal-close]').click()")
    page.wait_for_timeout(300)

    page.goto(BASE + "/dashboard/new/", wait_until="networkidle")
    shot(page, "06_editor", full=False, wait=900)
    warm_scroll(page)
    shot(page, "06b_editor_full", full=True, wait=400)

    page.goto(BASE + f"/dashboard/{SLUG}/edit/", wait_until="networkidle")
    page.click("[data-step-btn='2']")
    page.wait_for_timeout(500)
    shot(page, "07_editor_look", full=False)
    page.click("[data-step-btn='3']")
    page.wait_for_timeout(500)
    shot(page, "08_editor_photos")
    page.click("[data-step-btn='4']")
    page.wait_for_timeout(500)
    shot(page, "09_editor_share")

    page.goto(BASE + f"/letter/{SLUG}/", wait_until="networkidle")
    shot(page, "10_letter_opening", wait=1500)
    open_letter(page)
    shot(page, "11_letter_open", wait=6000)
    warm_scroll(page)
    shot(page, "12_letter_full", full=True, wait=800)

    page.goto(BASE + f"/letter/{LOCKED}/", wait_until="networkidle")
    shot(page, "13_locked_letter", wait=1200)

    page.goto(BASE + f"/letter/{DRAFT}/", wait_until="networkidle")
    shot(page, "14_draft_unavailable", wait=800)

    page.goto(BASE + "/accounts/signup/", wait_until="networkidle")
    shot(page, "15_signup", wait=600)

    # Mobile
    m = browser.new_context(
        viewport={"width": 390, "height": 844}, device_scale_factor=1,
        is_mobile=True, has_touch=True,
    )
    mp = m.new_page()
    mp.goto(BASE + "/", wait_until="networkidle")
    warm_scroll(mp)
    shot(mp, "20_mobile_home", full=True, wait=600)

    mp.goto(BASE + "/accounts/login/", wait_until="networkidle")
    mp.fill("#id_username", "demo")
    mp.fill("#id_password", "LoveLetter2026!")
    mp.click("button[type=submit]")
    mp.wait_for_load_state("networkidle")
    warm_scroll(mp)
    shot(mp, "21_mobile_dashboard", full=True, wait=700)

    mp.goto(BASE + "/dashboard/new/", wait_until="networkidle")
    shot(mp, "22_mobile_editor", full=False, wait=900)

    mp.goto(BASE + f"/letter/{SLUG}/", wait_until="networkidle")
    shot(mp, "23_mobile_letter", wait=1200)
    open_letter(mp)
    shot(mp, "24_mobile_letter_open", wait=5000)
    warm_scroll(mp)
    shot(mp, "25_mobile_letter_full", full=True, wait=700)

    mp.goto(BASE + f"/letter/{LOCKED}/", wait_until="networkidle")
    shot(mp, "26_mobile_locked", wait=1000)

    browser.close()

print("DONE", OUT)
