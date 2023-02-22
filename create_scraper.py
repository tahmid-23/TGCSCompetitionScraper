import mysql.connector
import requests
from bs4 import BeautifulSoup


def create_scraper(url, target_text):
    response = requests.get(url)
    response_html = response.text
    soup = BeautifulSoup(response_html, "html.parser")

    match = soup.find(string=target_text).parent
    path = []
    current_element = match
    while current_element.get("id") is None:
        if current_element.parent is None:
            break

        path.append(current_element.parent.index(current_element))
        current_element = current_element.parent

    path.reverse()
    path.insert(0, current_element.get("id"))
    return path


if __name__ == '__main__':
    experience_id = input("experience_id: ")
    update_url = input("update_url: ")
    target_text = input("target text: ")

    path = create_scraper(update_url, target_text)

    with mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user="tgcs",
            password="tgcs",
            database="tgcs_competition"
    ) as tgcs_db, tgcs_db.cursor() as cursor:
        cursor.execute("UPDATE experience SET update_url = %s WHERE experience_id = %s", (update_url, experience_id))
        cursor.execute("INSERT INTO scraper (experience_id, root) VALUES (%s, %s)", (experience_id, path[0]))
        scraper_id = cursor.lastrowid
        cursor.executemany("INSERT INTO scraper_path (scraper_id, `order`, `value`) VALUES (%s, %s, %s)", [(scraper_id, index, value) for index, value in enumerate(path[1:])])
        tgcs_db.commit()
