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

from zenml import step
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from agent.agent import Agent

# TODO making the return types Agent leads to some forward Ref errors
@step(enable_cache=True)
def get_agent(agent: Any) -> Any:
    """Returns the current agent with prompt and user-supplied tools.

    This is only a way to track configuration of the agent across versions.
    This agent is not a versioned object. You could call .tools on it and it
    would return the latest set of tools, unless you mention the version as
    argument.

    The versioned object is the type DeployedAgent.

    Args:
        agent: The current agent object.

    Returns:
        The same agent object so that it is tracked and versioned by ZenML.
    """
    return agent
