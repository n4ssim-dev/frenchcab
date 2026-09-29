from fastapi import FastAPI

from routes import courses, donnees

app = FastAPI(title="FrenchCab - API métier")

app.include_router(donnees.router)
app.include_router(courses.router)


@app.get("/health")
def health():
    return {"status": "ok"}
