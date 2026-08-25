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
            rideHeading: document.querySelector('#attractions-title')?.innerText.trim(),
            rideNames: [...document.querySelectorAll('.ride-card h3')]
                .map((item) => item.textContent.trim()),
            rideRouteLabels: [...document.querySelectorAll('.ride-card__media > span')]
                .map((item) => item.textContent.trim()),
            rideFacts: [...document.querySelectorAll('.ride-card ul')]
                .map((list) => [...list.children].map((item) => item.textContent.trim())),
            routeHeading: document.querySelector('#zone-title')?.innerText.trim(),
            routeSourceLabel: document.querySelector('.map-source')?.textContent.trim(),
            routeEntries: [...document.querySelectorAll('.story-entry')]
                .map((item) => item.textContent.trim()),
            dataRequest: Boolean(document.querySelector('.data-request')),
            dataModal: Boolean(document.querySelector('#data-modal')),
            heroRouteLines: document.querySelectorAll('#intro .route-line').length,
            countUpTargets: document.querySelectorAll('[data-countup]').length,
            routeLanes: [...document.querySelectorAll('.route-story header h3')]
                .map((item) => item.textContent.trim()),
            routeRideNodes: [...document.querySelectorAll('.story-attraction > strong')]
                .map((item) => item.textContent.trim()),
            routeFoodNodes: document.querySelectorAll('.story-food, .story-result--food').length,
            routeFoodLabels: [...document.querySelectorAll('.story-food > strong, .story-result--food > strong')]
                .map((item) => item.textContent.trim()),
            routeCatalogNumbers: document.querySelectorAll('.story-index, .story-step b').length,
            routeStepCounts: [...document.querySelectorAll('.story-steps')].map((list) => list.children.length),
            routeDisclaimer: document.querySelector('.story-disclaimer')?.textContent.trim(),
            mapImages: document.querySelectorAll('.park-map-base').length,
            rideOperationRows: document.querySelectorAll('.ride-card__operations > div').length,
            rideOperationValues: [...document.querySelectorAll('.ride-card__operations dd')]
                .map((item) => item.textContent.trim()),
            missingImages: [...document.images]
                .filter((image) => !image.complete || image.naturalWidth === 0)
                .map((image) => image.getAttribute('src')),
            metricValues: [...document.querySelectorAll('.metric-card strong')]
                .map((item) => item.textContent.trim()),
            metricSources: [...document.querySelectorAll('.metric-card small')]
                .map((item) => item.textContent.trim()),
            seasonShares: [...document.querySelectorAll('.season-share strong')]
                .map((item) => item.textContent.trim()),
            phoneLinks: [...document.querySelectorAll('a[href="tel:+79208539291"]')]
                .map((item) => item.textContent.trim()),
            leadButtons: document.querySelectorAll('[data-open-form]').length,
            applicationModal: Boolean(document.querySelector('#application-modal')),
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
    assert result["rides"] == 5, f"{name}: expected 5 ride cards"
    assert result["rideHeading"] == "Пять аттракционов.\nПять магнитов трафика.", f"{name}: attraction heading is outdated"
    assert result["rideNames"] == ["Бумеранг", "Вихрь", "Путь дракона", "Паук", "Смерч"], f"{name}: attraction composition is incorrect"
    assert result["rideRouteLabels"] == ["Молодёжный маршрут"] * 3 + ["Семейный маршрут"] * 2, f"{name}: attraction route labels are incorrect"
    assert result["rideFacts"] == [
        ["37,451 м", "85,32 км/ч", "303 м трек"],
        ["17,9 м", "47,916 км/ч", "392 м трек"],
        ["20,5 м", "63 км/ч", "377 м трек"],
        ["5 м", "6 об/мин", "от 120 см"],
        ["34,8 м", "15 об/мин", "от 140 см"],
    ], f"{name}: final technical facts are incorrect"
    assert result["routeHeading"] == "Что\nоткрываем", f"{name}: route heading was not rebuilt"
    assert result["routeSourceLabel"] == "Источник объектов · карта 2026", f"{name}: route source label is missing"
    assert result["routeEntries"] == [], f"{name}: directional inlet labels should be removed"
    assert not result["dataRequest"] and not result["dataModal"], f"{name}: finalization request should be removed"
    assert result["heroRouteLines"] == 0, f"{name}: decorative hero line should not cross the copy"
    assert result["countUpTargets"] >= 40, f"{name}: numeric animation coverage is incomplete"
    assert result["routeLanes"] == ["Молодёжной компании", "Семьи"], f"{name}: expected 2 audience stories"
    assert result["routeRideNodes"] == ["Бумеранг", "Вихрь", "Путь дракона", "Паук", "Смерч"], f"{name}: route attraction nodes are incorrect"
    assert result["routeFoodNodes"] == 6, f"{name}: expected 6 food contacts"
    assert result["routeFoodLabels"] == ["Блинная", "Сказочные крылья", "Бургерная + фудкорт", "Бум Вафля", "Базилик", "Общий фудкорт и посадка"], f"{name}: food route labels are incorrect"
    assert result["routeCatalogNumbers"] == 0, f"{name}: internal map numbers should not be displayed"
    assert result["routeStepCounts"] == [5, 4], f"{name}: route step sequences are incorrect"
    assert result["routeDisclaimer"].startswith("Распределение food-контактов — рабочая коммерческая модель"), f"{name}: working-model disclaimer is missing"
    assert result["mapImages"] == 0, f"{name}: route slide should not display the source map"
    assert result["rideOperationRows"] == 15, f"{name}: expected 15 attraction planning rows"
    assert result["rideOperationValues"] == [
        "20 человек", "590 чел./час", "на согласовании",
        "20 человек", "600 чел./час", "на согласовании",
        "16 человек", "480 чел./час", "на согласовании",
        "24 человека", "480 чел./час", "на согласовании",
        "56 человек", "1 120 чел./час", "на согласовании",
    ], f"{name}: attraction operating data are incorrect"
    assert not result["missingImages"], f"{name}: missing images {result['missingImages']}"
    assert result["scrollWidth"] <= width + 1, f"{name}: horizontal overflow {result['scrollWidth']} > {width}"
    assert not console_errors, f"{name}: console errors {console_errors}"
    assert "Новые аттракционы" in result["heroTitle"]
    assert result["metricValues"] == ["80+", "4,5 млн", "+35%", "1 200 ₽", "≈72%"], f"{name}: commercial metrics are incorrect"
    assert "Гостевые точки — 1 100 ₽ · точки Парка — ≈1 300 ₽" in result["metricSources"], f"{name}: check breakdown is missing"
    assert result["seasonShares"] == ["75%", "25%"], f"{name}: seasonality split is incorrect"
    assert len(result["phoneLinks"]) == 2 and all("+7 (920) 853-92-91" in item for item in result["phoneLinks"]), f"{name}: partner phone is missing"
    assert result["leadButtons"] == 0 and not result["applicationModal"], f"{name}: lead form should be removed"
    assert result["heroVideo"], f"{name}: hero video is missing"
    assert result["heroVideo"]["readyState"] >= 2, f"{name}: hero video did not load"
    assert 26 <= result["heroVideo"]["duration"] <= 28, f"{name}: unexpected hero video duration"
    assert result["heroVideo"]["muted"] and result["heroVideo"]["loop"] and result["heroVideo"]["playsInline"], f"{name}: hero video autoplay flags are incomplete"
    for selector in [".hero-title", ".hero-lead", ".hero-actions", ".hero-foot"]:
        box = page.locator(selector).bounding_box()
        assert box and box["y"] >= 0 and box["y"] + box["height"] <= height, f"{name}: {selector} is outside the hero viewport"

    page.screenshot(path=str(ARTIFACTS / f"{name}-hero.png"), full_page=False)

    page.locator("#numbers").evaluate("element => element.scrollIntoView({block: 'start', behavior: 'instant'})")
    page.wait_for_timeout(1200)
    assert page.locator(".metric-card [data-countup]").first.get_attribute("data-counted") == "true", f"{name}: metric count-up did not run"
    assert page.locator(".metric-card strong").all_inner_texts() == ["80+", "4,5 млн", "+35%", "1 200 ₽", "≈72%"], f"{name}: metric count-up did not finish"
    page.screenshot(path=str(ARTIFACTS / f"{name}-numbers.png"), full_page=False)

    page.locator("#zone").evaluate("element => element.scrollIntoView({block: 'start', behavior: 'instant'})")
    page.wait_for_timeout(1200)
    assert page.locator(".zone-composition dt").all_inner_texts() == ["3", "5", "6"], f"{name}: route summary count-up did not finish"
    page.screenshot(path=str(ARTIFACTS / f"{name}-zone.png"), full_page=False)
    page.locator("#zone").screenshot(path=str(ARTIFACTS / f"{name}-zone-section.png"))
    if name == "desktop":
        first_step = page.locator(".story-step").first
        first_step.hover()
        page.wait_for_timeout(250)
        assert first_step.evaluate("element => getComputedStyle(element).transform !== 'none'"), f"{name}: route hover animation is missing"
        page.mouse.move(10, 10)
        page.wait_for_timeout(350)
        assert first_step.evaluate("element => getComputedStyle(element).transform === 'none'"), f"{name}: route hover state does not return smoothly"

    page.locator("#attractions").evaluate("element => element.scrollIntoView({block: 'start', behavior: 'instant'})")
    page.wait_for_timeout(1200)
    assert page.locator("#attractions").evaluate("element => element.classList.contains('is-active')"), f"{name}: tall attraction slide did not activate"
    assert page.locator(".ride-card").first.evaluate("element => getComputedStyle(element).opacity === '1'"), f"{name}: attraction cards are not visible"
    page.screenshot(path=str(ARTIFACTS / f"{name}-attractions.png"), full_page=False)
    page.locator("#attractions").screenshot(path=str(ARTIFACTS / f"{name}-attractions-section.png"))

    page.locator("#offer").evaluate("element => element.scrollIntoView({block: 'start', behavior: 'instant'})")
    page.wait_for_timeout(1200)
    page.screenshot(path=str(ARTIFACTS / f"{name}-offer.png"), full_page=False)

    page.locator("#support").evaluate("element => element.scrollIntoView({block: 'start', behavior: 'instant'})")
    page.wait_for_timeout(1200)
    page.screenshot(path=str(ARTIFACTS / f"{name}-support.png"), full_page=False)

    page.locator("#join").evaluate("element => element.scrollIntoView({block: 'start', behavior: 'instant'})")
    page.wait_for_timeout(1200)
    page.screenshot(path=str(ARTIFACTS / f"{name}-join.png"), full_page=False)

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
