import os
from itertools import cycle
from pathlib import Path
from typing import Dict, List, Optional, Generator, Union, Literal

import yaml
from loguru import logger
from better_proxy import Proxy

from models import Account, Config


class ConfigurationError(Exception):
    """Base exception for configuration-related errors"""

    pass


class ConfigLoader:
    REQUIRED_PARAMS = frozenset(
        {"threads", "retry_limit", "imap_settings", "use_proxy"}
    )

    def __init__(self, base_path: Union[str, Path] = None):
        self.base_path = Path(base_path or os.getcwd())
        self.config_path = self.base_path / "config"
        self.data_path = self.config_path / "data"
        self.settings_path = self.config_path / "settings.yaml"

    @staticmethod
    def _read_file(file_path: Path, allow_empty: bool = False) -> List[str]:
        if not file_path.exists():
            raise ConfigurationError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8").strip()

        if not allow_empty and not content:
            raise ConfigurationError(f"File is empty: {file_path}")

        return [line.strip() for line in content.splitlines() if line.strip()]

    def _load_yaml(self) -> Dict:
        try:
            config = yaml.safe_load(self.settings_path.read_text(encoding="utf-8"))
            missing_fields = self.REQUIRED_PARAMS - set(config.keys())

            if missing_fields:
                raise ConfigurationError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )
            return config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML format: {e}")

    def _parse_proxies(self) -> Optional[List[Proxy]]:
        try:
            proxy_lines = self._read_file(
                self.data_path / "proxies.txt", allow_empty=True
            )
            if not proxy_lines:
                logger.warning("No proxies found")
                return None

            return [Proxy.from_str(line) for line in proxy_lines]
        except Exception as e:
            raise ConfigurationError(f"Failed to parse proxies: {e}")

    @staticmethod
    def _validate_email(email: str) -> bool:
        return "@" in email.strip()

    def _parse_accounts(
        self, mode: Literal["default", "oauth2"]
    ) -> Generator[Account, None, None]:
        try:
            for line in self._read_file(self.data_path / "accounts.txt"):
                try:
                    parts = None
                    for delimiter in [":", "|"]:
                        if delimiter in line:
                            parts = line.split(delimiter)
                            break

                    if not parts:
                        raise ValueError("No valid delimiter found")

                    if mode == "oauth2":
                        email, client_id, refresh_token = parts[0:3]
                        email = email.strip().replace("\n", "").replace("\r", "")
                        client_id = (
                            client_id.strip().replace("\n", "").replace("\r", "")
                        )
                        refresh_token = (
                            refresh_token.strip().replace("\n", "").replace("\r", "")
                        )

                        if not self._validate_email(email):
                            logger.warning(f"Skipping invalid email format: {email}")
                            continue

                        yield Account(
                            email=email,
                            client_id=client_id,
                            refresh_token=refresh_token,
                        )

                    else:
                        email, password = parts[0:2]
                        email = email.strip().replace("\n", "").replace("\r", "")
                        password = password.strip().replace("\n", "").replace("\r", "")

                        if not self._validate_email(email):
                            logger.warning(f"Skipping invalid email format: {email}")
                            continue

                        yield Account(
                            email=email,
                            password=password,
                        )

                except (ValueError, IndexError):
                    logger.warning(f"Skipping invalid account format: {line}")
                    continue

        except Exception as e:
            logger.error(f"Error processing accounts.txt: {e}")

    @staticmethod
    def _validate_domains(
        accounts: List[Account], domains: Dict[str, str]
    ) -> List[Account]:
        for account in accounts:
            domain = account.email.split("@")[1]

            if domain not in domains:
                raise ConfigurationError(
                    f"Domain '{domain}' is not supported, please add it to the config file"
                )
            account.imap_server = domains[domain]
        return accounts

    def load(self) -> Config:
        try:
            params = self._load_yaml()
            if params["use_proxy"]:
                proxies = self._parse_proxies()
                if not proxies:
                    raise SystemExit(1)
            else:
                proxies = []

            accounts = list(
                self._parse_accounts(
                    mode="default" if not params["use_oauth"] else "oauth2"
                )
            )
            if not accounts:
                raise ConfigurationError("No valid accounts found")

            validated_accounts = self._validate_domains(
                accounts, params["imap_settings"]
            )

            return Config(
                **params,
                accounts=validated_accounts,
                proxies=proxies,
            )

        except Exception as e:
            logger.error(f"Configuration loading failed: {e}")
            raise SystemExit(1)


def load_config() -> Config:
    return ConfigLoader().load()
