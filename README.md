````markdown
# LinkedIn Profile API & Intelligence Service

A production-grade, asynchronous backend API that reverse-engineers LinkedIn profile data[cite: 1], provides MongoDB caching, and generates structured AI-driven career insights.

---

## Architecture & System Overview

- **Web Framework:** FastAPI (Asynchronous request handling with strict Pydantic data modeling)
- **Database & Caching Layer:** MongoDB with `motor` (Asynchronous driver) for persistent document storage and sub-50ms cache hits
- **AI & NLP Analysis:** Multi-tier LangChain integration powered by Groq LLM with a rule-based deterministic fallback synthesis layer
- **Scraping Engine:** High-performance HTTP client configured with fallback parsing (Voyager identity endpoints, OpenGraph metadata, and JSON-LD schemas)
- **Containerization:** Production Docker image targeting lightweight Linux runtimes

---

## Approach & Engineering Design[cite: 1]

1. **API Reverse-Engineering**: Interacts with LinkedIn's internal REST-Li Voyager endpoints (`/voyager/api/identity/dash/profiles`) authenticated via session cookies (`li_at` and `JSESSIONID`)[cite: 1].
2. **Resilience & Fallback Strategy**: When authenticated endpoints hit checkpoints or rate limits, the scraper dynamically falls back to parsing OpenGraph tags and schema JSON-LD scripts embedded in the page markup.
3. **Storage & Caching Strategy**: Implements an asynchronous read-through cache using MongoDB (`motor`). Profiles are queried by unique handle; cache misses trigger a live scrape, generate AI insights, and cache the payload.
4. **Intelligence Layer**: Uses Groq LLMs (with deterministic heuristic fallbacks) to enrich extracted profile text with structured career summaries, level estimations, and core competencies.

---

## API Specification[cite: 1]

### **GET `/api/v1/profile`**[cite: 1]

Fetches structured profile metadata and AI insights for a given LinkedIn URL[cite: 1].

#### **Query Parameters**

| Parameter      | Type              | Required         | Description                                              |
| :------------- | :---------------- | :--------------- | :------------------------------------------------------- |
| `url`[cite: 1] | `string`[cite: 1] | **Yes**[cite: 1] | Fully qualified or partial LinkedIn profile URL[cite: 1] |

#### **Example Request**

```bash
curl -X 'GET' \
  '[https://your-deployed-service.onrender.com/api/v1/profile?url=https%3A%2F%2Fwww.linkedin.com%2Fin%2Fsamaltman%2F](https://your-deployed-service.onrender.com/api/v1/profile?url=https%3A%2F%2Fwww.linkedin.com%2Fin%2Fsamaltman%2F)' \
  -H 'accept: application/json'
```
````

#### **Example Response (`200 OK`)**

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

## Getting Started

### **1. Environment Configuration**

Create a `.env` file in the root directory:

```bash
cp .env.example .env

```

Populate your configuration variables:

```env
GROQ_API_KEY=your_groq_api_key_here
MONGO_URI=mongodb://localhost:27017
LINKEDIN_LI_AT=optional_cookie_token

```

### **2. Local Setup**

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

```

Interactive API documentation will be available at:

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

---

## Docker Deployment

```bash
# Build the Docker container
docker build -t tross-profile-scraper .

# Run container
docker run -d -p 8000:8000 --env-file .env --name tross-scraper tross-profile-scraper

```

---

## Known Limitations

- **Session Invalidation**: LinkedIn `li_at` authentication cookies expire periodically and must be manually refreshed in `.env`.

- **Voyager Schema Drift**: Internal LinkedIn Voyager payloads are undocumented and subject to upstream schema changes without notice.
- **Rate Limiting**: High-frequency concurrent requests to unauthenticated public endpoints are subject to LinkedIn IP-level CAPTCHA challenges.

```

```
