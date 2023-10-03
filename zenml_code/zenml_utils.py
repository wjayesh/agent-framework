

from typing import Dict, List, Optional
from zenml.client import Client

from tools.versioned_vector_store import VersionedVectorStoreTool
from zenml_code.pipelines.pipeline import PIPELINE_NAME


def get_existing_tools(versions: Optional[List[str]] = None, pipeline_version: Optional[int] = None) -> Dict[str, VersionedVectorStoreTool]:
        """Get the tools that already exist in the agent's toolkit.

        Args:
            versions: The versions of the tools to get. If none, 
            get all tools.
            pipeline_version: The version of the pipeline to get the tools from.

        Returns:
            The tools that already exist in the agent's toolkit.
        """
        all_tools = {}
        pipeline_model = Client().get_pipeline(
            name_id_or_prefix=PIPELINE_NAME, version=pipeline_version 
        )

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