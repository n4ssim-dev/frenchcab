from fastapi import FastAPI

from routes import donnees

app = FastAPI(title="FrenchCab - API métier")

app.include_router(donnees.router)


@app.get("/health")
def health():
    return {"status": "ok"}
