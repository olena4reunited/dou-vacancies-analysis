import asyncio
import csv
import re

import aiohttp
from aiohttp import ClientSession
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait

from scraper.config import CSV_SCHEMA, URLS_EXPERIENCE, TECHNOLOGIES


semaphore = asyncio.Semaphore()


def click_more_btn_while_displayed(driver: webdriver.Firefox):
    while True:
        try:
            more_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".more-btn a"))
            )
            if "display: none" in more_btn.get_attribute("style"):
                break

            more_btn.click()

        except Exception:
            break


def get_cleaned_date(date: str) -> str:
    cleaned_date = re.sub(r"\s+", " ", date).strip()
    date_parts = cleaned_date.split(" ")
    return " ".join(date_parts[:3])


def get_requirements(requirements: str):
    requirements = requirements.lower()
    requirements_set = set()

    for technology in TECHNOLOGIES:
        if re.search(r"\b" + re.escape(technology.lower()) + r"\b", requirements, re.IGNORECASE):
            requirements_set.add(technology)

    return list(requirements_set)


async def get_single_vacancy_info(session: ClientSession, url: str) -> dict:
    async with semaphore:
        async with session.get(url) as response:
            sourse_page = await response.text()
            soup = BeautifulSoup(sourse_page, "html.parser")

            date = soup.find("div", class_="date").text
            requirements = soup.find("div", class_="b-typo vacancy-section").text

            return {
                "title": soup.find("h1", class_="g-h2").text,
                "company": soup.find("div", class_="info").find("a").text,
                "date": get_cleaned_date(date),
                "requirements": get_requirements(requirements),
                "city": soup.find("span", class_="place").text,
            }


async def get_detail_vacancies_info(vacancies_list: list) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        tasks = []

        for vacancy in vacancies_list:
            task = get_single_vacancy_info(session, vacancy["url"])
            tasks.append(task)

        vacancies_info = await asyncio.gather(*tasks)

        for i, info in enumerate(vacancies_list):
            info["title"] = vacancies_info[i]["title"]
            info["company"] = vacancies_info[i]["company"]
            info["date"] = vacancies_info[i]["date"]
            info["requirements"] = vacancies_info[i]["requirements"]
            info["city"] = vacancies_info[i]["city"]

        return vacancies_list


def parse_page(driver: webdriver.Firefox, experience_level: str) -> list:
    click_more_btn_while_displayed(driver)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    vacancies = soup.find_all("li", class_="l-vacancy")

    vacancies_list = []

    for vacancy in vacancies:
        vacancies_list.append(
            {
                "url": vacancy.find("a").attrs["href"],
                "experience": experience_level,
            }
        )

    return vacancies_list


def write_to_csv(vacancies_list: list[dict]) -> None:
    with open("../data/vacancies.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_SCHEMA)

        for vacancy in vacancies_list:
            writer.writerow(
                [vacancy[column.lower()] for column in CSV_SCHEMA]
            )


async def main() -> None:
    opts = Options()
    opts.add_argument("--headless")

    driver = webdriver.Firefox(options=opts)

    all_vacancies = []

    for url, experience_level in URLS_EXPERIENCE:
        driver.get(url)
        vacancies_list = parse_page(driver, experience_level)
        detailed_vacancies_list = await get_detail_vacancies_info(vacancies_list)
        all_vacancies.extend(detailed_vacancies_list)

    write_to_csv(all_vacancies)

    driver.quit()


if __name__ == "__main__":
    asyncio.run(main())
