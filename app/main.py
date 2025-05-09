from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.api.routes import calculator

app = FastAPI(title="Fair Division Calculator")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(calculator.router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/calculator", response_class=HTMLResponse)
async def calculator_page(request: Request):
    return templates.TemplateResponse(
        "calculator.html",
        {"request": request}
    )

@app.get("/blog", response_class=HTMLResponse)
async def blog_index(request: Request):
    return templates.TemplateResponse(
        "blog/index.html",
        {"request": request}
    )

@app.get("/blog/{post_name}", response_class=HTMLResponse)
async def blog_post(request: Request, post_name: str):
    # Remove .html if it's in the post_name
    if post_name.endswith('.html'):
        post_name = post_name[:-5]
    return templates.TemplateResponse(
        f"blog/{post_name}.html",
        {"request": request}
    ) 