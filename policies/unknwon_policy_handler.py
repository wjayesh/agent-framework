from typing import Dict
from policies.available_policies import UnknownPolicies
from policies.base_unknown_policy import UnknownPolicy


class UnknownPolicyHandler:
    """A class that can register new policies and return them."""

    _policies: Dict[UnknownPolicies, UnknownPolicy] = {}

    @classmethod
    def register(cls, policy: UnknownPolicy) -> None:
        """Registers a new policy.

        Args:
            policy: The policy to register.
        """
        cls._policies[policy.TYPE] = policy

    @classmethod
    def get(cls, policy_type: UnknownPolicies) -> UnknownPolicy:
        """Returns the policy of the given type.

        Args:
            policy_type: The type of the policy to return.

        Returns:
            The policy of the given type.
        """
        return cls._policies[policy_type]