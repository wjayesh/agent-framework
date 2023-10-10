from policies.available_policies import UnknownPolicies
from policies.base_unknown_policy import UnknownPolicy
from policies.unknwon_policy_handler import UnknownPolicyHandler


class IgnorePolicy(UnknownPolicy):
    """Policy that returns a prompt to make the LLM give up."""
    TYPE = UnknownPolicies.IGNORE

    def _get_prompt(self, **kwargs) -> str:
        """Returns the prompt to be used by the agent."""
        return (
            "End the conversation and reply with a Final Answer "
            "'Sorry, I don't know the answer to that.'"
        )

    def _act(self, **kwargs) -> None:
        """Performs an action following the policy."""
        pass

UnknownPolicyHandler.register(IgnorePolicy)