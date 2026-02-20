from dotenv import load_dotenv
# Load environment variables immediately
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import engine, Base
from .routers import agent

app = FastAPI(title="CliniCall")

# Create tables on startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.include_router(agent.router)
from .routers import dashboard
app.include_router(dashboard.router)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("app/static/index.html")
@app.get("/dashboard-view")
@app.get("/dashboard")
def read_dashboard():
    return FileResponse("app/static/dashboard.html")
