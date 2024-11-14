from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait


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


def get_detail_vacancy_info(driver: webdriver.Firefox, vacancy_url: str):
    driver.get(vacancy_url)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    vacancy_details = {
        "title": soup.find("h1", class_="g-h2").text
    }

    return vacancy_details


def parse_page(driver: webdriver.Firefox, url: str):
    driver.get(url)
    click_more_btn_while_displayed(driver)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    vacancies = soup.find_all("a", class_="vt")
    vacancies_links = [url.get("href") for url in vacancies]

    vacancies_info = []

    for vacancy_link in vacancies_links:
        vacancies_info.append(get_detail_vacancy_info(driver, vacancy_link))

    return vacancies_info


def main():
    opts = Options()
    opts.add_argument("--headless")

    URL = "https://jobs.dou.ua/vacancies/?category=Python&exp=1-3"

    browser = webdriver.Firefox(options=opts)
    all_vacancies = parse_page(browser, URL)

    print(all_vacancies)



if __name__ == "__main__":
    main()
