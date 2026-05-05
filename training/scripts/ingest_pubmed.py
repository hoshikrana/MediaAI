import time
import json
import logging
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEARCH_QUERIES = {
    "pneumonia": "chest X-ray pneumonia findings radiology",
    "pleural_effusion": "pleural effusion chest radiograph diagnosis",
    "cardiomegaly": "cardiomegaly cardiac enlargement chest X-ray",
    "tuberculosis": "tuberculosis pulmonary chest radiograph findings",
    "normal_chest": "normal chest radiograph no significant finding"
}

def fetch_pubmed_abstracts(query: str, category: str, max_results=200) -> list[dict]:
    logger.info(f"Searching PubMed for: {category}")
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json", "usehistory": "y"}
    
    res = requests.get(search_url, params=params, timeout=30)
    res.raise_for_status()
    pmids = res.json().get("esearchresult", {}).get("idlist", [])
    
    results = []
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    
    for i in range(0, len(pmids), 20):
        batch = pmids[i:i+20]
        f_params = {"db": "pubmed", "id": ",".join(batch), "rettype": "abstract", "retmode": "xml"}
        f_res = requests.get(fetch_url, params=f_params, timeout=30)
        
        try:
            tree = ET.fromstring(f_res.content)
            for article in tree.findall(".//PubmedArticle"):
                pmid = article.findtext(".//PMID")
                title = article.findtext(".//ArticleTitle")
                abstract = article.findtext(".//AbstractText")
                year = article.findtext(".//PubDate/Year")
                
                if abstract and title:
                    results.append({
                        "pmid": pmid, "title": title, "abstract": abstract,
                        "year": year, "category": category
                    })
        except ET.ParseError:
            logger.error("XML parse error on a batch, skipping.")
        time.sleep(0.4) # Respect 3 req/sec rate limit
    return results

def main():
    out_file = Path("data/pubmed_raw.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    all_data = []
    completed_cats = set()
    
    if out_file.exists():
        all_data = json.loads(out_file.read_text())
        completed_cats = {d["category"] for d in all_data}
        logger.info(f"Resuming... found {len(all_data)} existing records.")
        
    for cat, query in SEARCH_QUERIES.items():
        if cat in completed_cats:
            continue
        data = fetch_pubmed_abstracts(query, cat)
        all_data.extend(data)
        out_file.write_text(json.dumps(all_data, indent=2))
        logger.info(f"Saved {len(data)} abstracts for {cat}.")

    logger.info(f"✅ PubMed ingestion complete. Total records: {len(all_data)}")

if __name__ == "__main__":
    main()
