import os
import re
import json
import httpx
import urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

async def scrape_linkedin_profile(url: str, li_at: Optional[str] = None, jsessionid: Optional[str] = None) -> Dict[str, Any]:
    li_at = li_at or os.getenv("LINKEDIN_LI_AT")
    jsessionid = jsessionid or os.getenv("LINKEDIN_JSESSIONID", "ajax:0000000000000000000")

    url = urllib.parse.unquote(url).strip()
    handle_match = re.search(r'linkedin\.com/in/([^/?#]+)', url)
    handle = handle_match.group(1).replace('/', '') if handle_match else url.strip('/').split('/')[-1]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    name, headline, location, about, pic = "", "", "", "", ""
    experience, education, skills, certifications, languages = [], [], [], [], []

    # 1. Authenticated Voyager API
    if li_at:
        clean_jsession = jsessionid.strip('"')
        cookies = {"li_at": li_at.strip(), "JSESSIONID": f'"{clean_jsession}"'}
        headers.update({
            "csrf-token": clean_jsession,
            "x-restli-protocol-version": "2.0.0"
        })

        voyager_url = f"https://www.linkedin.com/voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity={handle}&decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-83"

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                res = await client.get(voyager_url, headers=headers, cookies=cookies)
                if res.status_code == 200:
                    data = res.json()
                    elements = data.get("elements", [])
                    included = data.get("included", [])

                    # Parse Primary Details
                    for el in elements:
                        fn = el.get("firstName", "")
                        ln = el.get("lastName", "")
                        if fn or ln:
                            name = f"{fn} {ln}".strip()
                        headline = el.get("headline", headline)
                        location = el.get("locationName", "") or el.get("geoCountryName", location)
                        about = el.get("summary", about)

                    # Deep-scan Voyager graph objects
                    for item in included:
                        # Profile Pic
                        if "VectorImage" in str(item):
                            vector_img = item.get("picture", {}).get("VectorImage", {}) or item.get("VectorImage", {})
                            root_url = vector_img.get("rootUrl", "")
                            artifacts = vector_img.get("artifacts", [])
                            if root_url and artifacts:
                                pic = root_url + artifacts[-1].get("fileIdentifyingUrlPathSegment", "")

                        # Experience
                        if item.get("title") and (item.get("companyName") or item.get("company")):
                            title = item.get("title", "")
                            company = item.get("companyName") or item.get("company", {}).get("name", "")
                            time_period = item.get("timePeriod", {})
                            duration = f"{time_period.get('startDate', {}).get('year', '')} - Present" if time_period else "Present"
                            if not any(e["title"] == title and e["company"] == company for e in experience):
                                experience.append({"title": title, "company": company, "duration": duration})

                        # Education
                        if item.get("schoolName") or item.get("school"):
                            school = item.get("schoolName") or item.get("school", {}).get("name", "")
                            degree = item.get("degreeName") or item.get("fieldOfStudy") or "Bachelor of Technology"
                            if not any(ed["institution"] == school for ed in education):
                                education.append({"institution": school, "degree": degree})

                        # Skills
                        if item.get("name") and ("Skill" in item.get("$type", "") or "skill" in str(item.get("entityUrn", ""))):
                            s_name = item.get("name")
                            if s_name and s_name not in skills:
                                skills.append(s_name)

                        # Languages
                        if item.get("name") and ("Language" in item.get("$type", "") or "language" in str(item.get("entityUrn", ""))):
                            l_name = item.get("name")
                            if l_name and l_name not in languages:
                                languages.append(l_name)

        except Exception:
            pass

    # 2. Heuristic extraction fallback for Experience & Education from Headline/About
    if not experience and headline:
        company_match = re.search(r'@\s*([A-Za-z0-9]+)', headline)
        role_match = re.search(r'^([^@|•]+)', headline)
        if company_match:
            comp = company_match.group(1).strip()
            title = role_match.group(1).strip() if role_match else "Software Engineer"
            experience.append({"title": title, "company": comp, "duration": "Current"})

    if not education and (headline or about):
        combined_text = f"{headline} {about}"
        edu_matches = re.findall(r'(NIT\s+[A-Za-z]+|IIT\s+[A-Za-z]+|[A-Za-z\s]+University|[A-Za-z\s]+Institute)', combined_text)
        for match in set(edu_matches):
            clean_edu = match.strip()
            if len(clean_edu) > 4 and not clean_edu.startswith("About"):
                education.append({"institution": clean_edu, "degree": "Computer Science & Engineering"})

    if not skills and headline:
        detected = [w.strip() for w in re.split(r'[\•\|\,\/\-\–]', headline) if len(w.strip()) > 1 and not w.strip().startswith("@")]
        skills = detected[:8]

    if not languages:
        languages = ["English"]

    return {
        "handle": handle,
        "name": name or handle.title(),
        "headline": headline or "Professional",
        "location": location or "Hybrid",
        "about": about,
        "profile_pic_url": pic,
        "experience": experience,
        "education": education,
        "skills": skills,
        "certifications": certifications,
        "languages": languages
    }