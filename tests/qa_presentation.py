import os
import json
from pathlib import Path
from playwright.sync_api import sync_playwright


BASE_URL = f"http://127.0.0.1:{os.environ.get('PRESENTATION_PORT', '4173')}"
ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def inspect_page(page, name: str) -> dict:
    return page.evaluate(
        """(name) => ({
            name,
            width: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth,
            bodyScrollWidth: document.body.scrollWidth,
            slides: document.querySelectorAll('.slide').length,
            metrics: document.querySelectorAll('.metric-card').length,
            rides: document.querySelectorAll('.ride-card').length,
            missingImages: [...document.images]
                .filter((image) => !image.complete || image.naturalWidth === 0)
                .map((image) => image.getAttribute('src')),
            pendingValues: [...document.querySelectorAll('.metric-card strong')]
                .map((item) => item.textContent.trim()),
            heroTitle: document.querySelector('#intro-title')?.textContent.trim(),
            heroVideo: (() => {
                const video = document.querySelector('#hero-video');
                return video ? {
                    readyState: video.readyState,
                    duration: video.duration,
                    muted: video.muted,
                    loop: video.loop,
                    playsInline: video.playsInline,
                    paused: video.paused,
                } : null;
            })(),
        })""",
        name,
    )


def run_viewport(browser, width: int, height: int, name: str) -> dict:
    page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
    console_errors = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: console_errors.append(str(error)))
    response = page.goto(BASE_URL, wait_until="networkidle")
    assert response and response.ok, f"{name}: page response failed"
    page.wait_for_timeout(1200)
    page.wait_for_function("document.querySelector('#hero-video')?.readyState >= 2", timeout=15000)

    result = inspect_page(page, name)
    result["consoleErrors"] = console_errors

    assert result["slides"] == 7, f"{name}: expected 7 slides, got {result}"
    assert result["metrics"] == 5, f"{name}: expected 5 metrics"
    assert result["rides"] == 3, f"{name}: expected 3 ride cards"
    assert not result["missingImages"], f"{name}: missing images {result['missingImages']}"
    assert result["scrollWidth"] <= width + 1, f"{name}: horizontal overflow {result['scrollWidth']} > {width}"
    assert not console_errors, f"{name}: console errors {console_errors}"
    assert "Новые аттракционы" in result["heroTitle"]
    assert "—" in result["pendingValues"], f"{name}: pending business data should stay explicit"
    assert result["heroVideo"], f"{name}: hero video is missing"
    assert result["heroVideo"]["readyState"] >= 2, f"{name}: hero video did not load"
    assert 26 <= result["heroVideo"]["duration"] <= 28, f"{name}: unexpected hero video duration"
    assert result["heroVideo"]["muted"] and result["heroVideo"]["loop"] and result["heroVideo"]["playsInline"], f"{name}: hero video autoplay flags are incomplete"

    page.screenshot(path=str(ARTIFACTS / f"{name}-hero.png"), full_page=False)

    page.locator("#numbers").evaluate("element => element.scrollIntoView({block: 'start', behavior: 'instant'})")
    page.wait_for_timeout(1200)
    page.screenshot(path=str(ARTIFACTS / f"{name}-numbers.png"), full_page=False)

    page.locator("#zone").evaluate("element => element.scrollIntoView({block: 'start', behavior: 'instant'})")
    page.wait_for_timeout(1200)
    page.screenshot(path=str(ARTIFACTS / f"{name}-zone.png"), full_page=False)

    page.locator("#attractions").evaluate("element => element.scrollIntoView({block: 'start', behavior: 'instant'})")
    page.wait_for_timeout(1200)
    page.screenshot(path=str(ARTIFACTS / f"{name}-attractions.png"), full_page=False)

    page.locator("#offer").evaluate("element => element.scrollIntoView({block: 'start', behavior: 'instant'})")
    page.wait_for_timeout(1200)
    page.screenshot(path=str(ARTIFACTS / f"{name}-offer.png"), full_page=False)

    page.locator("#support").evaluate("element => element.scrollIntoView({block: 'start', behavior: 'instant'})")
    page.wait_for_timeout(1200)
    page.screenshot(path=str(ARTIFACTS / f"{name}-support.png"), full_page=False)

    page.locator("#join").evaluate("element => element.scrollIntoView({block: 'start', behavior: 'instant'})")
    page.wait_for_timeout(1200)
    page.screenshot(path=str(ARTIFACTS / f"{name}-join.png"), full_page=False)

    page.locator("[data-open-form]").click()
    assert page.locator("#application-modal").evaluate("dialog => dialog.open"), f"{name}: form modal did not open"
    page.locator("input[name='name']").fill("Тестовый контакт")
    page.locator("input[name='company']").fill("Тестовый проект")
    page.locator("input[name='contact']").fill("test@example.com")
    page.locator(".consent input").check()
    assert page.locator("#application-form").evaluate("form => form.checkValidity()"), f"{name}: valid form is invalid"
    page.locator("[data-close-modal]").first.click()
    assert not page.locator("#application-modal").evaluate("dialog => dialog.open"), f"{name}: form modal did not close"

    page.close()
    return result


def main() -> None:
    ARTIFACTS.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        results = [
            run_viewport(browser, 1440, 1000, "desktop"),
            run_viewport(browser, 768, 1024, "tablet"),
            run_viewport(browser, 390, 844, "mobile"),
        ]
        browser.close()

    for result in results:
        print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
