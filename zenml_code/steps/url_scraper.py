#  Copyright (c) ZenML GmbH 2023. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.

from typing import Dict, List
from agent.agent import URL

from steps.url_scraping_utils import get_all_pages, get_nested_readme_urls
from zenml import step


@step(enable_cache=True)
def url_scraper(
    scrapable_urls: Dict[str, List[URL]],
) -> Dict[str, List[URL]]:
    """Generates a list of relevant URLs to scrape.

    Args:
        scrapable_urls: A dictionary with version as key and list of URLs as value.

    Returns:
        A dictionary with version as key and list of URLs
    """
    # create a new dict with all the keys from scrapable_urls
    # and empty lists as values
    for version in scrapable_urls:
        for url in scrapable_urls[version]:
            if url.url.endswith("/"):
                # TODO think about how to incorporate
                # READMEs. Is this method okay?
                scrapable_urls[version].extend(get_all_pages(url.url))
            else:
                scrapable_urls[version].extend(get_nested_readme_urls(url.url))
            # remove duplicates
            scrapable_urls[version] = list(
                dict.fromkeys(scrapable_urls[version])
            )
    return scrapable_urls
