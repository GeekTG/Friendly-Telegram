#    Friendly Telegram Userbot
#    by GeekTG Team

import os
import requests


def main():
    port = os.environ.get("PORT", 8080)
    requests.get(f"http://localhost:{port}").raise_for_status()


if __name__ == "__main__":
    main()
