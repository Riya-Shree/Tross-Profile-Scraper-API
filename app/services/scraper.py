import os
import re
import json
import httpx
import urllib.parse
from pathlib import Path
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

    clean_jsession = jsessionid.strip('"')
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/vnd.linkedin.normalized+json+2.1",
        "csrf-token": clean_jsession,
        "x-restli-protocol-version": "2.0.0",
        "x-li-lang": "en_US"
    }
    
    cookies = {
        "li_at": li_at.strip() if li_at else "",
        "JSESSIONID": f'"{clean_jsession}"'
    }

    # Primary Live Voyager Endpoint
    voyager_url = f"https://www.linkedin.com/voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity={handle}&decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-83"

    name, headline, location, about, pic = "", "", "", "", ""
    experience, education, skills, certifications, languages = [], [], [], [], []

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            res = await client.get(voyager_url, headers=headers, cookies=cookies)
            print(f"--- LIVE SCRAPE STATUS: {res.status_code} ---")

            if res.status_code == 200:
                data = res.json()
                elements = data.get("elements", [])
                included = data.get("included", [])

                # Parse primary identity
                for el in elements:
                    fn = el.get("firstName", "")
                    ln = el.get("lastName", "")
                    if fn or ln:
                        name = f"{fn} {ln}".strip()
                    headline = el.get("headline", headline)
                    location = el.get("locationName", "") or el.get("geoCountryName", location)
                    about = el.get("summary", about)

                # Parse included sub-objects
                for item in included:
                    # Experience
                    if item.get("title") and (item.get("companyName") or item.get("company")):
                        t = item.get("title", "")
                        c = item.get("companyName") or item.get("company", {}).get("name", "")
                        time_obj = item.get("timePeriod", {})
                        start_yr = time_obj.get("startDate", {}).get("year", "")
                        dur = f"{start_yr} - Present" if start_yr else "Current"
                        if not any(e["title"] == t and e["company"] == c for e in experience):
                            experience.append({"title": t, "company": c, "duration": dur})

                    # Education
                    if item.get("schoolName") or item.get("school"):
                        sch = item.get("schoolName") or item.get("school", {}).get("name", "")
                        deg = item.get("degreeName") or item.get("fieldOfStudy") or "Degree"
                        if not any(ed["institution"] == sch for ed in education):
                            education.append({"institution": sch, "degree": deg})

                    # Skills
                    if item.get("name") and "Skill" in item.get("$type", ""):
                        s = item.get("name", "")
                        if s and s not in skills:
                            skills.append(s)

                    # Profile Photo
                    if "VectorImage" in str(item):
                        vec = item.get("picture", {}).get("VectorImage", {}) or item.get("VectorImage", {})
                        root = vec.get("rootUrl", "")
                        arts = vec.get("artifacts", [])
                        if root and arts:
                            pic = root + arts[-1].get("fileIdentifyingUrlPathSegment", "")

    except Exception as e:
        print(f"--- LIVE SCRAPE ERROR: {e} ---")

    # Fallback to headline keyword parsing if skills are empty
    if not skills and headline:
        detected = [w.strip() for w in re.split(r'[\•\|\,\/\-\–]', headline) if len(w.strip()) > 1 and not w.strip().startswith("@")]
        skills = detected[:6]

    return {
        "handle": handle,
        "name": name or handle.replace('-', ' ').title(),
        "headline": headline or "Professional",
        "location": location or "Bengaluru, Karnataka, India",
        "about": about,
        "profile_pic_url": pic,
        "experience": experience,
        "education": education,
        "skills": skills,
        "certifications": certifications,
        "languages": languages or ["English"]
    }