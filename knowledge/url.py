from pydantic import BaseModel
from knowledge.url_type import URLType


from typing import Optional


class URL(BaseModel):
    """A URL object."""

    url: str
    scrape: Optional[bool] = False
    url_type: Optional[URLType] = None

    def __init__(self, url: str, scrape: Optional[bool] = False, url_type: Optional[URLType] = None):
        """ "Create a URL object.

        Args:
            url: The URL to create.
            scrape: Whether or not to scrape the URL.
        """
        super().__init__(url=url, scrape=scrape)

        url_types = self.get_url_type(url)
        self.url_type = url_types

    # allow arbitrary types
    class Config:
        arbitrary_types_allowed = True

    def get_url_type(self, url: str) -> URLType:
        """Get the type of the URL.

        Args:
            url: The URL to get the type of.

        Returns:
            The type of the URL.
        """
        if "youtube.com" in url:
            return URLType.YOUTUBE
        elif "github.com" in url:
            return URLType.GITHUB
        elif "twitter.com" in url:
            return URLType.TWITTER
        elif "reddit.com" in url:
            return URLType.REDDIT
        elif "linkedin.com" in url:
            return URLType.LINKEDIN
        else:
            return URLType.WEBSITE
        # else:
        #     raise ValueError(
        #         "Invalid URL type. Only the following types are supported: {}".format(
        #             [t.name for t in URLType]
        #         )
        #     )

    @classmethod
    def url_exists(cls, url: str) -> bool:
        """Check if the URL exists.

        Args:
            url: The URL to check.

        Returns:
            True if the URL exists, False otherwise.
        """
        import requests

        try:
            response = requests.get(url)
        except requests.exceptions.ConnectionError:
            return False
        return response.status_code == 200

    def get_hash(self) -> str:
        """Get the hash of the URL.

        Args:
            url: The URL to get the hash of.

        Returns:
            The hash of the URL.
        """
        import hashlib

        return hashlib.sha256(self.url.encode()).hexdigest()
