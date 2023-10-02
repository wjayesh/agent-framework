from typing import List
from langchain.tools import VectorStoreQATool

class VersionedVectorStoreTool(VectorStoreQATool):
    urls: List[str]