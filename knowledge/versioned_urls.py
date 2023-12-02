from pydantic import BaseModel
from knowledge.url import URL


from typing import Dict, List, Optional


class VersionedURLs(BaseModel):
    """Versioned URLs."""

    # TODO maybe remove the optional requirement

    # version: Optional[str]
    # urls: Optional[List[URL]]

    dictionary: Optional[Dict[str, List[URL]]]