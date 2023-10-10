# the pipeline will take in a list of scrapable and non-scrapable URLs

from typing import Dict, List
from zenml import pipeline

from agent.agent import URL, Agent
from steps.url_scraper import url_scraper
from steps.web_url_loader import web_url_loader
from steps.index_generator import index_generator
from steps.get_tools import get_tools
from steps.get_agent import get_agent

PIPELINE_NAME = "index_creation_pipeline"

@pipeline(name=PIPELINE_NAME)
def index_creation_pipeline(
    project_name: str,
    urls: Dict[str, List[URL]],
    agent: Agent
) -> None:
    """Pipeline to create the index for the agent to use.

    Args:
        project_name: name of the project
        urls: dictionary with version as key and list of URLs as value
        agent: The agent object that triggered this pipeline.
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
    # TODO the last step should be get agent
    # which will take all the tools from the previous agent
    # and create a new agent based on the values of the current agent
    # values being the prompt that is being used, etc.
    all_tools = get_tools(project_name, vector_stores, scraped_urls)
    agent = get_agent(agent)

    return agent
