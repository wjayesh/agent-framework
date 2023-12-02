from __future__ import annotations
from typing import Dict, List, Optional
from zenml.client import Client
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.agent import Agent, InfraConfig

from tools.versioned_vector_store import VersionedVectorStoreTool
from zenml_code.pipelines.pipeline import index_creation_pipeline


"""
TODO
make this into a ZenML helper class, a singleton and store the 
pipeline models across calls. to optimize number of DB queries
"""


def get_existing_tools(
    pipeline_name: str,
    versions: Optional[List[str]] = None,
    pipeline_version: Optional[int] = None,
) -> Dict[str, VersionedVectorStoreTool]:
    """Get the tools that already exist in the agent's toolkit.

    Args:
        versions: The versions of the tools to get. If none,
        get all tools.
        pipeline_version: The version of the pipeline to get the tools from.

    Returns:
        The tools that already exist in the agent's toolkit.
    """
    all_tools = {}
    try:
        pipeline_model = Client().get_pipeline(
            name_id_or_prefix=pipeline_name, version=pipeline_version
        )
    except KeyError:
        # TODO should this be handled here or thrown to
        # the upper classes to be handled there?
        return all_tools

    if pipeline_model.runs is not None:
        # get the last run
        last_run = pipeline_model.runs[0]
        # get the agent_creator step
        all_tools_step = last_run.steps["get_tools"]

        # get the output of the step
        try:
            all_tools = all_tools_step.output.load()
            if versions is not None:
                all_tools = {version: all_tools[version] for version in versions}
        except ValueError:
            all_tools = {}

    return all_tools


def get_existing_agent(
    pipeline_name: str,
    pipeline_version: Optional[int] = None,
) -> Agent:
    """Returns an agent for the specified pipeline name and version."""
    pipeline_model = Client().get_pipeline(
        name_id_or_prefix=pipeline_name, version=pipeline_version
    )

    agent = None
    if pipeline_model.runs is not None:
        # get the last run
        last_run = pipeline_model.runs[0]
        # get the agent_creator step
        agent_step = last_run.steps["get_agent"]

        # get the output of the step
        try:
            agent = agent_step.output.load()
        except ValueError:
            # TODO should this be handled here or thrown to
            # the upper classes to be handled there?
            pass

    return agent


def trigger_pipeline(
    pipeline_name: str,
    project_name: str,
    urls: Dict[str, List[str]],
    infra_config: InfraConfig,
    agent: Agent,
) -> None:
    """Trigger the pipeline to create the index for the agent to use.

    Args:
        project_name: name of the project
        urls: dictionary with version as key and list of URLs as value
        infra_config: infrastructure configuration for the pipeline
    """
    # infra config will be used to set the stack in the future.
    # TODO call this index_creation_pipeline in a separate thread
    # to avoid blocking the main thread
    # TODO find out how to name a pipeline in code
    index_creation_pipeline(project_name, urls, agent)
