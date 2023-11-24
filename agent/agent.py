from enum import Enum
from typing import Dict, List, Optional, Tuple, cast
from langchain.base_language import BaseLanguageModel
from langchain.chains import LLMChain
from langchain.tools import BaseTool
from langchain.agents import ConversationalChatAgent
from agent.deployed_agent import DeployedAgent
from tools.versioned_vector_store import VersionedVectorStoreTool
import zenml_code.zenml_utils as zenml_utils


class URLType(Enum):
    WEBSITE = 0
    YOUTUBE = 1
    GITHUB = 2
    TWITTER = 3
    REDDIT = 4
    LINKEDIN = 5


class URL:
    def __init__(self, url: str, scrape: Optional[bool] = False):
        """ "Create a URL object.

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
            raise ValueError(
                "Invalid URL type. Only the following types are supported: {}".format(
                    [t.name for t in URLType]
                )
            )

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
    def __init__(
        self,
        base_url: str,
        latest_version: str,
        version_cutoff: str = None,
        skip_versions: List[str] = [],
    ):
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
        # TODO use pkg_resources.parse_version
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

    def get_urls(self) -> Dict[str, List[URL]]:
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


class Agent(ConversationalChatAgent):
    # this name should be unique and will be associated with the
    # pipeline name that backs the agent.
    name: str
    # this prompt should only define the personality
    # TODO make a prompt template and only take things like
    # a name and personality as input from the user
    prompt: str = ""
    _tools: List[BaseTool]
    _llm: BaseLanguageModel

    PREFIX: str = (
        "This is the W Agent and can answer questions on ZenML."
    )

    @classmethod
    def knowledge_tools(cls, name: str, version: str = None) -> List[BaseTool]:
        """Get all the tools available with the agent.

        This includes the user-defined tools along with those that
        the educate function generates.

        Args:
            version: The version of the agent to get the tools from.

        Returns:
            A list of all available tools.
        """
        # fetch all tools from the last step of the educate
        # pipeline and combine them with the tools that already
        # exist in the agent's toolkit

        # TODO when you implement deletion of a tool, just don't add
        # that tool to the list of tools
        knowledge_tools = zenml_utils.get_existing_tools(
            pipeline_name=name, pipeline_version=version
        ).values()
        return knowledge_tools

    def __init__(
        self,
        name: str,
        llm: Optional[BaseLanguageModel] = None,
        tools: Optional[List[BaseTool]] = None,
        config=None,
    ):
        """Create an agent object.

        Only the name is a required argument and it is unique to the agent.
        It is used to get the backing pipeline, data and tools associated with
        the agent. All other arguments are optional. However, while deploying the
        agent, an LLM should be configured and that can be achieved by calling
        the configure_llm method.

        Args:
            name: The name of the agent.
            llm: The language model to use.
            tools: The tools to use.
            config: The configuration to use.

        Returns:
            The agent object.
        """
        # TODO check if a pipeline with that name prefix exists
        # and add a warning that we are reusing the previous registered
        # agent. if you want a new one, create a different name.
        self.name = name
        self.config = config
        # TODO rename this to user-defined tools
        self.allowed_tools = tools
        self._llm = llm

    @property
    def llm(self) -> BaseLanguageModel:
        """Get the LLM Chain.

        Returns:
            The LLM Chain powering the agent's responses.
        """
        return self._llm

    def get_allowed_tools(self, version: str = None) -> List[BaseTool]:
        """Get all the tools available with the agent.

        This includes the user-defined tools along with those that
        the educate function generates.

        Args:
            version: The version of the agent to get the tools from.

        Returns:
            A list of all available tools.
        """
        # fetch all tools from the last step of the educate
        # pipeline and combine them with the tools that already
        # exist in the agent's toolkit

        # TODO when you implement deletion of a tool, just don't add
        # that tool to the list of tools
        knowledge_tools = Agent.knowledge_tools(name=self.name, version=version)
        knowledge_tools.extend(self.allowed_tools)
        # i have added the allowed tools thing here just to implement
        # the agent abstraction. i would love to go back to using just
        # _tools in the future.
        knowledge_tools.extend(self._tools)
        return knowledge_tools

    def add_tool(self, tool: VersionedVectorStoreTool):
        self._tools.append(tool)

    def remove_tool(self, tool: VersionedVectorStoreTool):
        """You can only remove a tool that you have added yourself.

        We can however implement a simple hack for all tools, like i mentioned
        in the TODO above.
        """
        self._tools.remove(tool)

    def configure_llm(self, llm: BaseLanguageModel):
        self._llm = llm

    def _get_new_data_urls(
        self,
        project_name: str,
        existing_tools: Dict[str, VersionedVectorStoreTool],
        docs: Documentation,
        general_urls: List[URL],
    ) -> Dict[str, List[URL]]:
        """Get the URLs that have not been indexed yet.

        Args:
            existing_tools: The tools that already exist in the agent's toolkit.
            docs: The documentation to get the URLs from.
            general_urls: Any URLs that the agent should derive knowledge from.

        Returns:
            A dict of URLs with version as key and a list of URLs as values.
        """
        # initialize a dict of versioned URLs
        versioned_urls: Dict[str, List[URL]] = {
            docs.global_latest_version: general_urls
        }

        # get the URLs from the documentation
        docs_urls = docs.get_urls()

        # merge versioned_urls and docs_urls
        for version, urls in docs_urls.items():
            versioned_urls[version].extend(urls)

        # get the URLs that have not been indexed yet
        for version in existing_tools:
            # if the name of the tool does not match the project name,
            # skip the tool.
            tool = existing_tools[version]
            names = tool.name.split("-")
            if names[0] != project_name:
                continue
            # get the URLs that have not been indexed yet
            versioned_urls[version] = [
                url
                for url in versioned_urls[version]
                if url.get_hash() not in tool.urls
            ]

        return versioned_urls

    def educate(
        self,
        project_name: str,
        docs: Documentation,
        general_urls: List[URL],
        infra_config: Optional[InfraConfig] = None,
    ):
        """Educate the agent on a set of documents.

        TODO take a parameter to specify if the general URLs should be
        associated with the version of the documentation or not.
        If not, then we create separate collections for all of them, with
        an LLM summarized description of the contents of the URL.
        Also take in a date of publication along with the URL.

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

        # TODO if every pipeline name has the project name, then this becomes easier
        # since you only get the tools for that specific project.
        # get the list of tools already a part of the agent's toolkit
        existing_tools = zenml_utils.get_existing_tools(pipeline_name=self.name)

        # make a list of hashed URLs a part of the tool definition.
        # TODO: in the future, make a part of the custom vector store?
        # get URLs that have not been indexed yet
        new_urls = self._get_new_data_urls(
            project_name=project_name,
            existing_tools=existing_tools,
            docs=docs,
            general_urls=general_urls,
        )

        # TODO maybe have a different pipeline name for each project?
        # call the zenml pipeline to create the index
        zenml_utils.trigger_pipeline(
            pipeline_name=self.name,
            project_name=project_name,
            urls=new_urls,
            infra_config=infra_config,
            agent=self
        )

    # define check status should check for completion of pipeline and also
    # outout the pipeline version being run. can be used for deploy.

    # define get_versions for the agent to show all available versions
    # (pipeline versions)

    def deploy(self, version: int) -> DeployedAgent:
        """Deploy the agent.

        Deploy the agent at some endpoint.

        Args:
            version: the version of the agent to deploy.
        """

        deployed_agent = DeployedAgent(
            agent=zenml_utils.get_existing_agent(
                pipeline_name=self.name, pipeline_version=version
            ),
            version=version,
        )

        # create a service out of it and deploy locally
        return deployed_agent


"""
my agent should extend the conversational agent and implement the 
create prompt method. override the agent.get_allowed_tools



inside the get agent step, add the pipeline version to the version
property of the agent. orr do it inside the get agent utils fn 
this property is optional, if none present, none used. 
all fns that expect version will want to get it from this property if present
otherwise check for fn inputs (ulta).
"""
