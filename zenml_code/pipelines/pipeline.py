# the pipeline will take in a list of scrapable and non-scrapable URLs

from typing import Dict, List
from zenml import pipeline

from agent.agent import URL
from steps.url_scraper import url_scraper
from steps.web_url_loader import web_url_loader
from steps.index_generator import index_generator
from steps.get_tools import get_tools

PIPELINE_NAME = "index_creation_pipeline"

@pipeline(name=PIPELINE_NAME)
def index_creation_pipeline(
    project_name: str,
    urls: Dict[str, List[URL]],
) -> None:
    """Pipeline to create the index for the agent to use.

    Args:
        project_name: name of the project
        urls: dictionary with version as key and list of URLs as value
    """
    # create scrapable and non-scrapable URLs maps
    # depending on the value of url.scrape
    scrapable_urls = {}
    non_scrapable_urls = {}
    for version in urls:
        scrapable_urls[version] = []
        non_scrapable_urls[version] = []
        for url in urls[version]:
            if url.scrape:
                scrapable_urls[version].append(url)
            else:
                non_scrapable_urls[version].append(url)
    
    scraped_urls = url_scraper(scrapable_urls)
    # merge scraped_urls and non_scrapable_urls
    for version in non_scrapable_urls:
        scraped_urls[version].extend(non_scrapable_urls[version])
    documents = web_url_loader(scraped_urls)
    vector_stores = index_generator(documents)
    all_tools = get_tools(project_name, vector_stores, scraped_urls)

    return all_tools
