from abc import abstractmethod
from typing import Any, Dict

from policies.available_policies import UnknownPolicies

class UnknownPolicy:
    """A base class that all unknown policies should implement."""
    TYPE: UnknownPolicies

    @abstractmethod
    def _get_prompt(self, **kwargs) -> str:
        """Returns the prompt to be used by the agent.
        """

    @abstractmethod
    def _act(self, **kwargs) -> None:
        """Performs an action following the policy.
        """

    def implement(self, intermediate_steps: Dict[str, Any], **kwargs) -> str:
        """Implements the policy.

        Args:
            intermediate_steps: The intermediate steps from the agent execution.

        Returns:
            Returns a prompt to the model following the policy.
        """
        # add the intermediate steps to the kwargs
        kwargs["intermediate_steps"] = intermediate_steps
        # perform the action
        self._act(**kwargs)
        # return a prompt to the model
        return self._get_prompt(**kwargs)
        