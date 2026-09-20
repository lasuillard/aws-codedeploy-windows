from fastapi import FastAPI, HTTPException, status

from src.scrapers.errors import AuthenticationError
from src.scrapers.kftc import KftcScraper
from src.scrapers.kftc.datamodels import KftcLoginCredential

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {err!s}",
        ) from err

    return {"message": "Login completed."}
