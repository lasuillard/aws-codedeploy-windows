from fastapi import FastAPI

from src.scrapers.errors import AuthenticationError
from src.scrapers.kftc import KftcScraper
from src.scrapers.kftc.scraper import KftcLoginCredential

app = FastAPI()


@app.get("/")
def health_check():
    return "OK"


@app.post("/kftc/login")
def kftc_login(login_credential: KftcLoginCredential):
    scraper = KftcScraper()
    try:
        with scraper:
            scraper.login(login_credential)
    except AuthenticationError as err:
        return {"error": f"Login failed: {err!s}"}

    return {"message": "Login completed."}
