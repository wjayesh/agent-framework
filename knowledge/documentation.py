from knowledge.url import URL


from typing import Dict, List, Tuple


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

    def _enumerate_versions(self) -> Tuple[List[str], str]:
        """Enumerate versions from the latest to the version cutoff.

        Returns:
            A list of versions and the latest version.
        """
        versions = []
        # TODO use pkg_resources.parse_version
        # decrement minor versions and then major versions step by step
        # until the version cutoff is reached.
        version = self.latest_version
        if self.version_cutoff is None:
            # TODO choose sane value here
            return [self.latest_version], self.latest_version
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