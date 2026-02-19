from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from .database import engine, Base
from .routers import agent

# Load environment variables
load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CliniCall")

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
