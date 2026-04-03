from pathlib import Path

from playwright.sync_api import sync_playwright


PROFILE_DIR = Path("freshful_profile").resolve()


def main():
    print(f"Profil persistent: {PROFILE_DIR}")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1440, "height": 1800},
            args=[
                "--start-maximized",
            ],
        )

        page = context.new_page()
        page.goto("https://www.freshful.ro", wait_until="domcontentloaded")

        print()
        print("1. Acceptă cookies")
        print("2. Loghează-te")
        print("3. Setează adresa / localitatea / slotul de livrare")
        print("4. Deschide produsul și verifică dacă vezi promoția reală")
        print()
        input("Când totul este pregătit, apasă Enter aici... ")

        print("Profilul a rămas salvat în folderul freshful_profile.")
        context.close()


if __name__ == "__main__":
    main()