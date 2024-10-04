from setuptools import setup, find_packages

setup(
    name="mastodon_tools",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "appdirs",
        "Click",
        "python-dateutil",
        "pytz",
        "requests_cache",
        "validate_email_address",
        "yarl",
    ],
    entry_points={
        "console_scripts": [
            "mastodon-swimmer=mastodon_tools.scripts.mastodon_swimmer:cli",
            "mastodon-user=mastodon_tools.scripts.mastodon_user:cli",
        ],
    },
)
