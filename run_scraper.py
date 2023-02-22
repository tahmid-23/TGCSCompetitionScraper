import sys

import mysql.connector
import requests
from bs4 import BeautifulSoup
from termcolor import cprint


def run_scraper(url, path):
    response = requests.get(url)
    response_html = response.text
    soup = BeautifulSoup(response_html, "html.parser")

    current_element = None
    if path[0] is not None:
        current_element = soup.find(id=path[0])

    for index in path[1:]:
        current_element = current_element.contents[index]

    return current_element.text


if __name__ == "__main__":
    print("Updating database...")

    with mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="tgcs",
        password="tgcs",
        database="tgcs_competition"
    ) as tgcs_db, tgcs_db.cursor() as cursor:
        cursor.execute("SELECT experience_id, name, update_url FROM experience")
        experiences = cursor.fetchall()

        for (experience_id, name, update_url) in experiences:
            print(f"Updating {name}...")
            if update_url is None:
                print(f"No update url for {name}, skipping...")
                continue

            cursor.execute("SELECT scraper_id, root FROM scraper WHERE experience_id = %s", (experience_id,))
            scrapers = cursor.fetchall()

            if len(scrapers) == 0:
                print(f"No scrapers for {name}, skipping...")

            dates = []
            for (scraper_id, root) in scrapers:
                cursor.execute("SELECT value FROM scraper_path WHERE scraper_id = %s ORDER BY `order`", (scraper_id,))
                path = [value for (value,) in cursor.fetchall()]
                path.insert(0, root)

                try:
                    new_date = run_scraper(update_url, path).strip()
                except:
                    print(f"A {name} scraper failed.", file=sys.stderr)
                    continue
                dates.append(new_date)

            dates.sort()

            cursor.execute("SELECT date_id, description FROM important_date WHERE experience_id = %s", (experience_id,))
            old_dates_result = cursor.fetchall()

            old_dates = [date[1] for date in old_dates_result]
            old_dates.sort()

            if dates == old_dates:
                print(f"No new dates for {name}, skipping...")
                continue

            print("Old dates:")
            for date in old_dates:
                cprint(f"- {date}", "red")
            print()

            print("New dates:")
            for date in dates:
                cprint(f"+ {date}", "green")
            print()

            should_update = input("Update important dates? Y/N ")
            while should_update.lower() != "y" and should_update.lower() != "n":
                should_update = input("Invalid response, please type Y/N ")

            if should_update.lower() == "y":
                cursor.executemany("DELETE FROM important_date WHERE date_id = %s", [(old_date[0],) for old_date in old_dates_result])
                cursor.executemany("INSERT INTO important_date (experience_id, description) VALUES(%s, %s)", [(experience_id, date) for date in dates])

            tgcs_db.commit()
