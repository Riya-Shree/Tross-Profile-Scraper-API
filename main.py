# import re
# from fastapi import FastAPI, Query, HTTPException
# # Change from:
# # from app.services.scraper import scrape_linkedin_profile, parse_linkedin_data

# # To wherever your working scraper function is located:
# from app.services.scraper import scrape_linkedin_profile, parse_linkedin_data
# from app.services.ai_service import generate_ai_insights
# from app.db.mongodb import profiles_collection

# app = FastAPI(title="Tross Profile Scraper API")

# def extract_handle(url: str) -> str:
#     match = re.search(r'linkedin\.com/in/([^/?#]+)', url)
#     if not match:
#         raise HTTPException(status_code=400, detail="Invalid LinkedIn profile URL")
#     return match.group(1).rstrip('/')

# @app.get("/api/v1/profile")
# async def get_profile(url: str = Query(..., description="LinkedIn profile URL")):
#     if not url.startswith("http://") and not url.startswith("https://"):
#         url = f"https://{url}"

#     # Extract clean handle
#     handle_match = re.search(r'linkedin\.com/in/([^/?#]+)', url)
#     handle = handle_match.group(1).rstrip('/') if handle_match else url.rstrip('/').split('/')[-1]

#     # 1. MongoDB Cache Check
#     try:
#         cached_doc = await profiles_collection.find_one({"handle": handle}, {"_id": 0})
#         if cached_doc:
#             return {"source": "cache", "data": cached_doc["data"]}
#     except Exception:
#         pass  # If DB connection fails temporarily, continue to live scrape

#     # 2. Scrape Profile
#     try:
#         raw_scraped = await scrape_linkedin_profile(url)
#         parsed_data = parse_linkedin_data(raw_scraped)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

#     # 3. AI Insights
#     ai_insights = await generate_ai_insights(
#         name=parsed_data["name"],
#         headline=parsed_data["headline"],
#         about=parsed_data["about"],
#         skills=parsed_data["skills"]
#     )
#     parsed_data["ai_insights"] = ai_insights

#     # 4. Save to Cache ONLY if scraping & AI succeeded
#     has_valid_insights = (
#         parsed_data.get("ai_insights") 
#         and "Could not generate insights" not in str(parsed_data["ai_insights"].get("summary", ""))
#     )
#     if has_valid_insights:
#         try:
#             await profiles_collection.update_one(
#                 {"handle": handle},
#                 {"$set": {"url": url, "handle": handle, "data": parsed_data}},
#                 upsert=True
#             )
#         except Exception:
#             pass

#     return {"source": "live", "data": parsed_data}


import re
from fastapi import FastAPI, Query, HTTPException
from app.services.scraper import scrape_linkedin_profile
from app.services.ai_service import generate_ai_insights
from app.db.mongodb import profiles_collection

app = FastAPI(title="Tross Profile Scraper API")

@app.get("/api/v1/profile")
async def get_profile(url: str = Query(..., description="LinkedIn profile URL")):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://{url}"

    # Extract clean handle
    handle_match = re.search(r'linkedin\.com/in/([^/?#]+)', url)
    handle = handle_match.group(1).rstrip('/') if handle_match else url.rstrip('/').split('/')[-1]

    # 1. MongoDB Cache Check
    try:
        cached_doc = await profiles_collection.find_one({"handle": handle}, {"_id": 0})
        if cached_doc:
            return {"source": "cache", "data": cached_doc["data"]}
    except Exception:
        pass  # If DB connection fails temporarily, continue to live scrape

    # 2. Scrape Profile
    try:
        # We only need this one call! It returns the parsed dictionary directly.
        parsed_data = await scrape_linkedin_profile(url)
        
        if "error" in parsed_data:
             raise HTTPException(status_code=400, detail=parsed_data["error"])
             
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

    # 3. AI Insights
    ai_insights = await generate_ai_insights(
        name=parsed_data.get("name", ""),
        headline=parsed_data.get("headline", ""),
        about=parsed_data.get("about", ""),
        skills=parsed_data.get("skills", [])
    )
    parsed_data["ai_insights"] = ai_insights

    # 4. Save to Cache ONLY if scraping & AI succeeded
    has_valid_insights = (
        parsed_data.get("ai_insights") 
        and "Could not generate insights" not in str(parsed_data["ai_insights"].get("summary", ""))
    )
    if has_valid_insights:
        try:
            await profiles_collection.update_one(
                {"handle": handle},
                {"$set": {"url": url, "handle": handle, "data": parsed_data}},
                upsert=True
            )
        except Exception:
            pass

    return {"source": "live", "data": parsed_data}