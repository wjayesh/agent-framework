from enum import Enum
from typing import Dict, List, Optional, Tuple, cast
from langchain.base_language import BaseLanguageModel
from tools.versioned_vector_store import VersionedVectorStoreTool
import zenml_utils


class URLType(Enum):
    WEBSITE = 0
    YOUTUBE = 1
    GITHUB = 2
    TWITTER = 3
    REDDIT = 4
    LINKEDIN = 5

class URL:
    def __init__(self, url: str, scrape: Optional[bool] = False):
        """"Create a URL object.

        Args:
            url: The URL to create.
            scrape: Whether or not to scrape the URL.
        """
        self.url = url
        self.scrape = scrape

        type = self.get_url_type(url)
        self.type = type

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
            raise ValueError("Invalid URL type. Only the following types are supported: {}".format([t.name for t in URLType]))


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

class Documentation:
    def __init__(self, base_url: str, latest_version: str, version_cutoff: str = None, skip_versions: List[str] = []):
        """Create a Documentation object.

        A Documentation object needs to have a latest version object at the moment
        because there might be no other way to know what a version look like for a
        project. All other arguments are optional, save for the base URL.

        Args:
            base_url: The base URL of the documentation.
            latest_version: The latest version of the documentation.
            version_cutoff: The version to stop indexing at.
            skip_versions: Any versions to skip.
        """
        self.base_url = base_url
        self.latest_version = latest_version
        self.version_cutoff = version_cutoff
        self.skip_versions = skip_versions

    def _enumerate_versions(self) -> Tuple[List[int], str]:
        """Enumerate versions from the latest to the version cutoff.

        Returns:
            A list of versions and the latest version.
        """
        versions = []
        # decrement minor versions and then major versions step by step
        # until the version cutoff is reached.
        version = self.latest_version
        while version != self.version_cutoff:
            versions.append(version)
            # decrement minor version
            version = version.split(".")
            version[1] = str(int(version[1]) - 1)
            version = ".".join(version)
            # decrement major version
            if version == self.version_cutoff:
                break
            version = version.split(".")
            version[0] = str(int(version[0]) - 1)
            version[1] = "0"
            version = ".".join(version)

        # TODO
        return versions, global_latest_version

    def get_urls(self)-> Dict[str, List[URL]]:
        """Returns valid URLs for different versions of the documentation.

        TODO One limitation is that the version needs to be present in the URL
        as per the currrent implementation. I want this to be derived from a
        non-versioned base URL too.

        Returns:
            A dict of URLs with version as key and a list of URLs as values.
        """
        # figure out where the version string is in the base URL
        # and create a template out of it
        template = self.base_url.replace(self.latest_version, "{}")

        # prepare a list of versions iterating from the latest to the version
        # cutoff, skipping any versions in the skip_versions list
        self.versions, self.global_latest_version = self._enumerate_versions()
        # create a list of URLs from latest to version cutoff, skipping
        # any version in the skip_versions list. Also check if such a
        # URL exists or is reachable.
        urls = {}
        for version in self.versions:
            url = template.format(version)
            if URL.url_exists(url):
                urls[version] = [URL(url, scrape=True)]
        return urls


class InfraConfig:
    def __init__(self, orchestrator: str, credentials: str):
        """Create an InfraConfig object.

        Args:
            orchestrator: The orchestrator to use.
            credentials: The credentials to use.
        """
        self.orchestrator = orchestrator
        self.credentials = credentials
        
class VersionedURLs:
    def __init__(self, urls: List[URL], version: str):
        """Create a VersionedURLs object.

        Args:
            urls: The URLs to create.
            version: The version of the URLs.
        """
        self.urls = urls
        self.version = version

    def get_urls(self) -> List[URL]:
        """Get the URLs.

        Returns:
            The URLs.
        """
        return self.urls

    def get_version(self) -> str:
        """Get the version.

        Returns:
            The version.
        """
        return self.version

class Agent:
    _tools: List[VersionedVectorStoreTool]
    _llm: BaseLanguageModel

    def __init__(self, llm: BaseLanguageModel, tools: List[VersionedVectorStoreTool], config):
        self.config = config
        self._llm = llm
        self._tools = tools

    @property
    def llm(self):
        return self._llm
    
    @property
    def tools(self):
        return self._tools

    def add_tool(self, tool: VersionedVectorStoreTool):
        self._tools.append(tool)

    def remove_tool(self, tool: VersionedVectorStoreTool):
        self._tools.remove(tool)

    def configure_llm(self, llm: BaseLanguageModel):
        self._llm = llm

    def _get_new_data_urls(self, project_name: str, existing_tools: List[VersionedVectorStoreTool], docs: Documentation, general_urls: List[URL]) -> List[URL]:
        """Get the URLs that have not been indexed yet.

        Args:
            existing_tools: The tools that already exist in the agent's toolkit.
            docs: The documentation to get the URLs from.
            general_urls: Any URLs that the agent should derive knowledge from.

        Returns:
            A list of URLs that have not been indexed yet.
        """
        # initialize a dict of versioned URLs
        versioned_urls: Dict[str, List[URL]] = {docs.global_latest_version: []}

        # get the URLs from the documentation
        docs_urls = docs.get_urls()

        # merge versioned_urls and docs_urls
        for version, urls in docs_urls.items():
            versioned_urls[version].extend(urls)

        # get the URLs that have not been indexed yet
        new_urls = []
        for tool in existing_tools:
            # get the version from the name of the tool
            # the first part is the name of the project.
            # if it doesn't match, skip the tool.
            names = tool.name.split("-")
            if names[0] != project_name:
                continue
            version = names[1]

            # for a given version, get all URLs in versioned_urls whose
            # hash is not present in tool_urls
            for url in versioned_urls[version]:
                if url.get_hash() not in tool.urls:
                    new_urls.append(url)

        return new_urls
    
    def educate(self, project_name: str, docs: Documentation, general_urls: List[URL], infra_config: Optional[InfraConfig] = None):
        """Educate the agent on a set of documents.

        Take the input documentation and URLs and create vector
        database collections out of it. Make them into tools and add to
        the agent's toolkit. This function should only create these
        collections for data that has not been seen yet.

        Args:
            project_name: The name of the project to create the tools for.
            docs: The documentation to educate the agent on.
            general_urls: Any URLs that the agent should derive knowledge from.
                Can be a website, a link to a YouTube video, etc.
            infra_config: The infrastructure configuration to use to run the
                index creation.
        """
        docs_urls = docs.get_urls()
        cast(List[URL], docs_urls)

        # get the list of tools already a part of the agent's toolkit
        existing_tools = zenml_utils.get_existing_tools()

        # make a list of hashed URLs a part of the tool definition.
        # TODO: in the future, make a part of the custom vector store?
        # get URLs that have not been indexed yet
        new_urls = self._get_new_data_urls(existing_tools, docs_urls.extend(general_urls))

        # call the zenml pipeline to create the index
        zenml_utils.trigger_pipeline(project_name, new_urls, infra_config)
