from fastapi import FastAPI

from routes import courses, donnees, predictions,reservations

app = FastAPI(title="FrenchCab - API métier")

app.include_router(donnees.router)
app.include_router(courses.router)
app.include_router(predictions.router)
app.include_router(reservations.router)

@app.get("/health")
def health():
    return {"status": "ok"}
