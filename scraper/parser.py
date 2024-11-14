import csv
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait

from scraper.config import CSV_SCHEMA, URLS_EXPERIENCE, TECHNOLOGIES


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


def get_detail_vacancy_info(driver: webdriver.Firefox, vacancy_url: str):
    driver.get(vacancy_url)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    date = soup.find("div", class_="date").text.strip()

    body = soup.find("div", class_="vacancy-section").text

    vacancy_details = {
        "title": soup.find("h1", class_="g-h2").text,
        "company": soup.find("div", class_="info").find("a").text,
        "date": get_cleaned_date(date),
        "url": vacancy_url,
        "requirements": get_requirements(body),
        "city": soup.find("span", class_="place").text,
    }

    return vacancy_details


def parse_page(driver: webdriver.Firefox, url: str):
    global experience_level
    driver.get(url)
    click_more_btn_while_displayed(driver)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    vacancies = soup.find_all("a", class_="vt")
    vacancies_links = [url.get("href") for url in vacancies]

    vacancies_info = []

    for vacancy_link in vacancies_links:
        vacancies_info.append(get_detail_vacancy_info(driver, vacancy_link))

    for url_level, level in URLS_EXPERIENCE:
        if url_level == url:
            experience_level = level
            break

    for vacancy in vacancies_info:
        vacancy["experience"] = experience_level

    return vacancies_info


def write_to_csv(vacancies_list: list[dict]):
    with open("../data/vacancies.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_SCHEMA)

        for vacancy in vacancies_list:
            writer.writerow(
                [vacancy[column.lower()] for column in CSV_SCHEMA]
            )


def main():
    opts = Options()
    opts.add_argument("--headless")

    browser = webdriver.Firefox(options=opts)

    all_vacancies = []

    for url in URLS_EXPERIENCE:
        all_vacancies.extend(parse_page(browser, url[0]))

    write_to_csv(all_vacancies)


if __name__ == "__main__":
    main()
