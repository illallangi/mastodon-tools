from yarl import URL
import requests
from requests.exceptions import RequestException
from json import JSONDecodeError
from validate_email_address import validate_email


class MastodonUser:
    """
    Represents a Mastodon user.

    This class provides properties to access various parts of the user's email address,
    the Webfinger URL for the user, the Webfinger data, the activity URL for the user,
    and the base URL of the Mastodon server the user is on.
    """

    def __init__(self, email: str):
        """
        Initialize a MastodonUser instance.

        Args:
            email (str): The user's email address.

        Raises:
            ValueError: If the email address is not valid.
        """
        # Validate the email address
        if not validate_email(email):
            raise ValueError(f"{email} is not a valid email address")

        # Store the email address
        self.email = email

    @property
    def local_part(self) -> str:
        """Get the local part of the email address (before the @)."""
        return self.email.split("@")[0]

    @property
    def domain(self) -> str:
        """Get the domain of the email address (after the @)."""
        return self.email.split("@")[1]

    @property
    def webfinger_url(self) -> URL:
        """Get the Webfinger URL for the user."""
        return URL(
            f"https://{self.domain}/.well-known/webfinger?resource=acct:{self.email}"
        )

    @property
    def webfinger(self) -> dict:
        """
        Get the Webfinger data for the user.

        This property makes a GET request to the Webfinger URL and parses the response as JSON.

        Raises:
            RequestException: If the GET request fails.
            JSONDecodeError: If the response cannot be decoded as JSON.
        """
        try:
            # Make a GET request to the Webfinger URL
            response = requests.get(
                self.webfinger_url,
            )
            # Raise an exception if the request failed
            response.raise_for_status()
            # Parse the response as JSON and return it
            return response.json()
        except RequestException as e:
            raise RequestException(f"Failed to get Webfinger data: {e}")
        except JSONDecodeError as e:
            raise JSONDecodeError(
                f"Failed to decode response as JSON: {e.doc}, {e.pos}"
            )

    @property
    def activity_url(self) -> URL:
        """
        Get the activity URL for the user.

        This property extracts the activity URL from the Webfinger data.
        """
        # Extract the activity URL from the Webfinger data and return it
        return URL(
            next(
                link
                for link in self.webfinger["links"]
                if link.get("type") == "application/activity+json"
                and link.get("rel") == "self"
            )["href"]
        )

    @property
    def mastodon_server(self) -> URL:
        """
        Get the base URL of the Mastodon server the user is on.

        This property removes the path and query from the activity URL to get the base URL.
        """
        # Remove the path and query from the activity URL to get the base URL and return it
        return self.activity_url.with_path("").with_query({})

    @property
    def directory_url(self) -> URL:
        """
        Get the directory URL for the user.

        This property constructs the directory URL from the Mastodon server base URL.
        """
        # Construct the directory URL from the Mastodon server base URL and return it
        return self.mastodon_server / "api" / "v1" / "directory"

    @property
    def directory(self) -> dict:
        """
        Get the directory data for the user.

        This property makes a GET request to the directory URL and parses the response as JSON,
        and stores each profile in a dictionary with the profile uri as the key.

        It handles pagination by checking if the "next" link is present in the response,
        and updating the URL accordingly.

        Returns:
            dict: A dictionary of profiles, with the profile uri as the key.

        Raises:
            RequestException: If the GET request fails.
            JSONDecodeError: If the response cannot be decoded as JSON.
        """
        # Initialize an empty dictionary to store the profiles
        result = {}
        # Format the directory URL with the limit
        url = self.directory_url % {"limit": 10, "local": "true"}
        try:
            while True:
                # Make a GET request to the directory URL
                response = requests.get(
                    url,
                )
                # Raise an exception if the request failed
                response.raise_for_status()
                # Get the links from the response
                links = response.links
                # Parse the response as JSON
                response = response.json()

                # Loop over the profiles in the response
                for profile in response:
                    # Store each profile in the result dictionary with the profile uri as the key
                    result[profile["uri"]] = profile

                # If there is no "next" link in the response, break the loop
                if "next" not in links:
                    break

                # Update the URL to the "next" link
                url = URL(links["next"]["url"])
        except RequestException as e:
            raise RequestException(f"Failed to get directory data: {e}")
        except JSONDecodeError as e:
            raise JSONDecodeError(
                f"Failed to decode response as JSON: {e.doc}, {e.pos}"
            )
        # Return the result dictionary
        return result

    @property
    def profile(self) -> dict:
        """
        Get the profile data for the user.

        This property returns the profile that matches the user's activity URL in the directory data.

        Returns:
            dict: The profile data for the user.

        Raises:
            StopIteration: If no matching profile is found in the directory data.
        """

        if self.activity_url.human_repr() in self.directory:
            return self.directory[self.activity_url.human_repr()]

        raise StopIteration("No matching profile found in directory data.")

    @property
    def profile_id(self) -> str:
        """
        Get the profile ID for the user.

        This property extracts the profile ID from the profile data.
        """
        # Extract the profile ID from the profile data and return it
        return self.profile["id"]

    @property
    def statuses_url(self) -> URL:
        """
        Get the status URL for the user.

        This property constructs the status URL from the Mastodon server base URL.
        """
        # Construct the status URL from the Mastodon server base URL and return it
        return (
            self.mastodon_server
            / "api"
            / "v1"
            / "accounts"
            / self.profile_id
            / "statuses"
        )

    @property
    def statuses(self) -> dict:
        """
        Fetches the statuses from the Mastodon API.

        This function makes a GET request to the statuses URL, parses the response as JSON,
        and stores each status in a dictionary with the status ID as the key.

        It handles pagination by checking if the "next" link is present in the response,
        and updating the URL accordingly.

        Returns:
            dict: A dictionary of statuses, with the status ID as the key.

        Raises:
            RequestException: If the GET request fails.
            JSONDecodeError: If the response cannot be decoded as JSON.
        """
        # Initialize an empty dictionary to store the statuses
        result = {}
        # Format the statuses URL with the limit
        url = self.statuses_url % {"limit": 10}
        try:
            # Loop until there are no more pages of statuses
            while True:
                # Make a GET request to the status URL
                response = requests.get(
                    url,
                )
                # Raise an exception if the request failed
                response.raise_for_status()
                # Get the links from the response
                links = response.links
                # Parse the response as JSON
                response = response.json()

                # Loop over the statuses in the response
                for status in response:
                    # Store each status in the result dictionary with the status ID as the key
                    result[status["id"]] = status

                # If there is no "next" link in the response, break the loop
                if "next" not in links:
                    break

                # Update the URL to the "next" link
                url = URL(links["next"]["url"])
        except RequestException as e:
            # If a RequestException is raised, re-raise it with a custom message
            raise RequestException(f"Failed to get status data: {e}")
        except JSONDecodeError as e:
            # If a JSONDecodeError is raised, re-raise it with a custom message
            raise JSONDecodeError(
                f"Failed to decode response as JSON: {e.doc}, {e.pos}"
            )
        # Return the result dictionary
        return result
