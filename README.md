# ⚡ LinkedIn Profile Intelligence API

🚀 **Live API Endpoint:** [Click here to test via Swagger UI](https://tross-profile-scraper-api.onrender.com/docs)

**High-performance, asynchronous LinkedIn profile scraping & AI analysis engine**

---

## 📌 Overview

An asynchronous RESTful API engineered to reverse engineer LinkedIn APIs and build a hosted API that accepts a LinkedIn profile URL and returns most of the information available on the profile page as structured JSON. It manages database read-through caching via MongoDB, and synthesizes structured career profiles using LangChain and Groq LLMs.

### ✨ Key Features

- **Profile Extraction**: Retrieves details such as name, headline, location, about, experience, education, skills, certifications, languages, and profile images when available.
- **Voyager & Fallback Engine**: Uses a reverse-engineered approach incorporating your own Linkedin credentials in the backend for primary extraction, alongside resilient OpenGraph and JSON-LD schema fallbacks.
- **Production-Ready Architecture**: Designed to deploy the API publicly over HTTPS.
- **Secure Handling**: Keeps all credentials and secrets out of the repository.

---

## 🏗️ Approach & Engineering Design

1. **API Reverse-Engineering**: Interacts with LinkedIn's internal REST-Li Voyager endpoint (`/voyager/api/identity/dash/profiles`) using authenticated cookies to reverse engineer LinkedIn APIs.
2. **Dynamic Fallback Pipeline**: If endpoints encounter verification walls or rate limits, the scraper parses OpenGraph metadata and JSON-LD schema blocks from public pages.
3. **Storage & Caching Layer**: Asynchronous read-through cache powered by `motor`. Uncached profiles trigger a live scrape and AI generation, then persist to MongoDB with a unique handle index.
4. **Heuristic & AI Synthesis**: Enriches raw profile text using Groq LLM chains with a deterministic heuristic fallback to guarantee uptime.

---

## 🚀 API Documentation

### `GET /api/v1/profile`

Accepts a LinkedIn profile URL as input and returns a structured JSON response.

#### Parameters

| Parameter | Type     | Required | Description                              |
| :-------- | :------- | :------: | :--------------------------------------- |
| `url`     | `string` | **Yes**  | Accepts a LinkedIn profile URL as input. |

#### Request Example

```bash
curl -X 'GET' '[https://tross-profile-scraper-api.onrender.com/api/v1/profile?url=https%3A%2F%2Fwww.linkedin.com%2Fin%2Fsamaltman%2F](https://tross-profile-scraper-api.onrender.com/api/v1/profile?url=https%3A%2F%2Fwww.linkedin.com%2Fin%2Fsamaltman%2F)' -H 'accept: application/json'
```

#### Response Example (`200 OK`)

```json
{
  "source": "live",
  "data": {
    "handle": "samaltman",
    "name": "Sam Altman",
    "headline": "CEO at OpenAI",
    "location": "San Francisco Bay Area",
    "profile_pic_url": "[https://media.licdn.com/dms/image/](https://media.licdn.com/dms/image/)...",
    "about": "Co-founder and CEO at OpenAI...",
    "experience": [
      {
        "title": "CEO",
        "company": "OpenAI",
        "duration": "Present"
      }
    ],
    "education": [
      {
        "institution": "Stanford University",
        "degree": "Computer Science"
      }
    ],
    "skills": [
      "Artificial Intelligence",
      "Distributed Systems",
      "Executive Leadership"
    ],
    "certifications": [
      {
        "name": "Certified Cloud & Distributed Systems Specialist",
        "issuer": "Technical Authority"
      }
    ],
    "languages": ["English"],
    "ai_insights": {
      "summary": "Sam Altman is an experienced engineering and technology leader specializing in building scalable software systems and frontier AI infrastructure.",
      "key_strengths": [
        "Scalable Backend Engineering",
        "API System Design",
        "Cloud Infrastructure"
      ],
      "career_level": "Senior",
      "recommended_roles": [
        "Senior Backend Engineer",
        "Distributed Systems Engineer",
        "AI/ML Solutions Engineer"
      ]
    }
  }
}
```

---

## 🛠️ Setup Instructions

### 1. Prerequisites

- Python 3.10+
- MongoDB instance running locally on port `27017` (or MongoDB Atlas URI)

### 2. Environment Configuration

Create an environment configuration file, ensuring to keep all credentials and secrets out of the repository:

```bash
cp .env.example .env
```

Fill in the configuration keys (you may use your own Linkedin credentials in the backend):

```env
GROQ_API_KEY=your_groq_api_key_here
MONGO_URI=mongodb://localhost:27017
LINKEDIN_LI_AT=optional_linkedin_cookie_token
```

### 3. Local Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive Documentation**: `http://localhost:8000/docs`
- **Alternative Specification**: `http://localhost:8000/redoc`

---

## 🐳 Docker Deployment

Run the complete application stack inside isolated containers:

```bash
docker build -t tross-profile-scraper .
docker run -d -p 8000:8000 --env-file .env --name tross-scraper tross-profile-scraper
```

Using Docker Compose:

```bash
docker compose up --build -d
```

---

## ⚠️ Known Limitations

As required, here are the known limitations of this scraping approach:

- **Session Expiration**: LinkedIn `li_at` session tokens expire periodically and require manual updates in `.env`.
- **Voyager Schema Changes**: Internal LinkedIn API responses are undocumented and subject to upstream payload restructuring.
- **Anti-Scraping Defenses**: High-frequency concurrent requests to unauthenticated endpoints may trigger IP-level CAPTCHA verification walls.
