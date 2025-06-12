from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.api.routes import calculator
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from collections import Counter
import textstat

app = FastAPI(title="Fair Division Calculator")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(calculator.router, prefix="/api")


nltk.download("punkt")
nltk.download("stopwords")

stop_words = set(stopwords.words("english"))

@app.get("/metrics", response_class=HTMLResponse)
async def metrics_form(request: Request):
    return templates.TemplateResponse("metrics_form.html", {"request": request})

@app.post("/metrics", response_class=HTMLResponse)
async def metrics_result(request: Request, user_text: str = Form(...)):
    words = word_tokenize(user_text)
    sentences = sent_tokenize(user_text)
    word_count = len(words)
    char_count = len(user_text)
    avg_sentence_length = word_count / len(sentences) if sentences else 0
    stopword_count = sum(1 for w in words if w.lower() in stop_words)
    stopword_ratio = stopword_count / word_count if word_count else 0
    flesch_score = textstat.flesch_reading_ease(user_text)

    non_stopwords = [w.lower() for w in words if w.lower() not in stop_words]
    counts = Counter(non_stopwords)
    repeated_words = sum(1 for count in counts.values() if count > 1)
    repetition_ratio = repeated_words / len(counts) if counts else 0

    metrics = {
        "Word Count": word_count,
        "Character Count": char_count,
        "Avg Sentence Length": round(avg_sentence_length, 2),
        "Stopword Ratio": round(stopword_ratio, 2),
        "Flesch Reading Ease": round(flesch_score, 2),
        "Repetition Ratio": round(repetition_ratio, 2),
    }

    return templates.TemplateResponse("metrics_result.html", {"request": request, "metrics": metrics})





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