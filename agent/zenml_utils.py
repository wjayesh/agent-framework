

from typing import List, Optional

from tools.versioned_vector_store import VersionedVectorStoreTool


def get_existing_tools(version: Optional[int] = None) -> List[VersionedVectorStoreTool]:
        """Get the tools that already exist in the agent's toolkit.

        Returns:
            A list of tools that already exist in the agent's toolkit.
        """
        # get the list of tools already a part of the agent's toolkit
        