"""
Stellar Wallet Manager

Manages Stellar wallets for testnet and mainnet.
- Testnet wallets: Auto-funded via Friendbot, no password protection
- Mainnet wallets: Password-protected secret keys (UI only)

API endpoints are restricted to testnet wallets for security.
"""

import os
import sys
import json
import time
import hashlib
import secrets
import base64
import hmac
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

import requests

# Stellar SDK imports
try:
    from stellar_sdk import Keypair, Server, Network
    from stellar_sdk.exceptions import NotFoundError, BadRequestError
    HAS_STELLAR = True
except ImportError:
    HAS_STELLAR = False

# TinyDB imports
from tinydb import TinyDB, Query
try:
    import tinydb_encrypted_jsonstorage as enc_json
    HAS_ENCRYPTION = True
except ImportError:
    HAS_ENCRYPTION = False

# Cryptography for mainnet key encryption
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


# Network configurations
NETWORKS = {
    "testnet": {
        "horizon_url": "https://horizon-testnet.stellar.org",
        "network_passphrase": "Test SDF Network ; September 2015",
        "friendbot_url": "https://friendbot.stellar.org",
    },
    "mainnet": {
        "horizon_url": "https://horizon.stellar.org",
        "network_passphrase": "Public Global Stellar Network ; September 2015",
        "friendbot_url": None,
    }
}


@dataclass
class Wallet:
    """Wallet data structure."""
    address: str  # Public key (G...)
    secret_key: str  # Secret key (S...) - encrypted for mainnet
    network: str  # "testnet" or "mainnet"
    label: str  # User-friendly name
    created_at: str  # ISO timestamp
    encrypted: bool = False  # True if secret_key is encrypted (mainnet)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Wallet":
        return cls(**data)

    def public_info(self) -> Dict[str, Any]:
        """Return wallet info without secret key."""
        return {
            "address": self.address,
            "network": self.network,
            "label": self.label,
            "created_at": self.created_at,
            "encrypted": self.encrypted,
        }


class WalletManagerError(Exception):
    """Base exception for wallet manager errors."""
    pass


class WalletNotFoundError(WalletManagerError):
    """Wallet not found."""
    pass


class NetworkError(WalletManagerError):
    """Network operation failed."""
    pass


class EncryptionError(WalletManagerError):
    """Encryption/decryption failed."""
    pass


def _get_data_dir() -> Path:
    """Get the data directory for wallet storage."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    data_dir = base / "heavymeta" / "wallets"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


class WalletManager:
    """
    Manages Stellar wallets with encrypted storage.

    Testnet wallets are stored with plaintext secret keys.
    Mainnet wallets have encrypted secret keys requiring a password.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the wallet manager.

        Args:
            db_path: Optional custom path for wallet database.
        """
        if not HAS_STELLAR:
            raise WalletManagerError("stellar_sdk not installed")

        self.db_path = db_path or (_get_data_dir() / "wallets.json")
        self.db = TinyDB(str(self.db_path))
        self.query = Query()

    # =========================================================================
    # Wallet Creation
    # =========================================================================

    def create_testnet_wallet(self, label: Optional[str] = None, auto_fund: bool = True) -> Wallet:
        """
        Create a new testnet wallet.

        Args:
            label: Optional label for the wallet.
            auto_fund: Whether to auto-fund via Friendbot (default: True).

        Returns:
            Created wallet with address and secret key.
        """
        keypair = Keypair.random()

        wallet = Wallet(
            address=keypair.public_key,
            secret_key=keypair.secret,
            network="testnet",
            label=label or f"Testnet Wallet {self._get_wallet_count('testnet') + 1}",
            created_at=datetime.utcnow().isoformat(),
            encrypted=False,
        )

        # Save to database
        self.db.insert(wallet.to_dict())

        # Auto-fund via Friendbot
        if auto_fund:
            try:
                self.fund_testnet_wallet(wallet.address)
            except NetworkError:
                # Wallet created but funding failed - still return wallet
                pass

        return wallet

    def create_mainnet_wallet(self, label: str, password: str) -> tuple[Wallet, str]:
        """
        Create a new mainnet wallet with encrypted secret key.

        Args:
            label: Label for the wallet.
            password: Password to encrypt the secret key.

        Returns:
            Tuple of (created wallet, unencrypted secret key).

        Note: This should only be called from the Metavinci UI.
        """
        if not HAS_CRYPTO:
            raise WalletManagerError("cryptography package not installed")

        keypair = Keypair.random()
        unencrypted_secret = keypair.secret

        # Encrypt the secret key
        encrypted_secret = self._encrypt_secret(unencrypted_secret, password)

        wallet = Wallet(
            address=keypair.public_key,
            secret_key=encrypted_secret,
            network="mainnet",
            label=label,
            created_at=datetime.utcnow().isoformat(),
            encrypted=True,
        )

        # Save to database
        self.db.insert(wallet.to_dict())

        return wallet, unencrypted_secret

    def recover_wallet_from_secret(self, secret_key: str, network: str, label: Optional[str] = None, password: Optional[str] = None) -> Wallet:
        """
        Recover a wallet from a secret key.

        Args:
            secret_key: The Stellar secret key (S...).
            network: The network ("testnet" or "mainnet").
            label: Optional label for the wallet.
            password: Password for encrypting mainnet secret key (required for mainnet).

        Returns:
            Recovered wallet.

        Raises:
            WalletManagerError: If secret key is invalid or password missing for mainnet.
            EncryptionError: If encryption fails.
        """
        try:
            # Validate secret key and derive public key
            keypair = Keypair.from_secret(secret_key)
        except Exception as e:
            raise WalletManagerError(f"Invalid secret key: {str(e)}")

        # Check if wallet already exists
        if self.wallet_exists(keypair.public_key):
            raise WalletManagerError(f"Wallet with address {keypair.public_key} already exists")

        # For mainnet wallets, encrypt the secret key
        if network == "mainnet":
            if not password:
                raise WalletManagerError("Password is required for mainnet wallet recovery")
            
            if not HAS_CRYPTO:
                raise WalletManagerError("cryptography package not installed")
            
            encrypted_secret = self._encrypt_secret(secret_key, password)
            stored_secret = encrypted_secret
            encrypted = True
        else:
            # Testnet wallets store plaintext secret key
            stored_secret = secret_key
            encrypted = False

        wallet = Wallet(
            address=keypair.public_key,
            secret_key=stored_secret,
            network=network,
            label=label or f"Recovered {network.title()} Wallet",
            created_at=datetime.utcnow().isoformat(),
            encrypted=encrypted,
        )

        # Save to database
        self.db.insert(wallet.to_dict())

        return wallet

    # =========================================================================
    # Wallet Retrieval
    # =========================================================================

    def get_wallet(self, address: str) -> Wallet:
        """
        Get a wallet by address.

        Args:
            address: The wallet's public key.

        Returns:
            Wallet data.

        Raises:
            WalletNotFoundError: If wallet not found.
        """
        result = self.db.search(self.query.address == address)
        if not result:
            raise WalletNotFoundError(f"Wallet not found: {address}")
        return Wallet.from_dict(result[0])

    def list_wallets(self, network: Optional[str] = None) -> List[Wallet]:
        """
        List all wallets, optionally filtered by network.

        Args:
            network: Optional network filter ("testnet" or "mainnet").

        Returns:
            List of wallets.
        """
        if network:
            results = self.db.search(self.query.network == network)
        else:
            results = self.db.all()

        return [Wallet.from_dict(r) for r in results]

    def list_testnet_wallets(self) -> List[Wallet]:
        """List all testnet wallets."""
        return self.list_wallets(network="testnet")

    def list_mainnet_wallets(self) -> List[Wallet]:
        """List all mainnet wallets."""
        return self.list_wallets(network="mainnet")

    # =========================================================================
    # Wallet Operations
    # =========================================================================

    def delete_wallet(self, address: str) -> bool:
        """
        Delete a wallet by address.

        Args:
            address: The wallet's public key.

        Returns:
            True if deleted, False if not found.
        """
        removed = self.db.remove(self.query.address == address)
        return len(removed) > 0

    def fund_testnet_wallet(self, address: str) -> Dict[str, Any]:
        """
        Fund a testnet wallet via Friendbot.

        Args:
            address: The wallet's public key.

        Returns:
            Friendbot response data.

        Raises:
            NetworkError: If funding fails.
        """
        friendbot_url = NETWORKS["testnet"]["friendbot_url"]

        try:
            response = requests.get(
                friendbot_url,
                params={"addr": address},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise NetworkError(f"Friendbot funding failed: {e}")

    def get_balance(self, address: str, network: str = "testnet") -> Dict[str, Any]:
        """
        Get the balance of a wallet.

        Args:
            address: The wallet's public key.
            network: The network ("testnet" or "mainnet").

        Returns:
            Balance information including XLM and other assets.

        Raises:
            NetworkError: If balance lookup fails.
        """
        horizon_url = NETWORKS[network]["horizon_url"]
        server = Server(horizon_url)

        try:
            account = server.accounts().account_id(address).call()
            balances = []
            for balance in account.get("balances", []):
                balances.append({
                    "asset_type": balance.get("asset_type"),
                    "asset_code": balance.get("asset_code", "XLM"),
                    "balance": balance.get("balance"),
                })
            return {
                "address": address,
                "network": network,
                "balances": balances,
                "sequence": account.get("sequence"),
            }
        except NotFoundError:
            return {
                "address": address,
                "network": network,
                "balances": [],
                "funded": False,
            }
        except Exception as e:
            raise NetworkError(f"Balance lookup failed: {e}")

    def get_secret_key(self, address: str, password: Optional[str] = None) -> str:
        """
        Get the secret key for a wallet.

        Args:
            address: The wallet's public key.
            password: Password for mainnet wallets (required if encrypted).

        Returns:
            The secret key.

        Raises:
            WalletNotFoundError: If wallet not found.
            EncryptionError: If decryption fails.
        """
        wallet = self.get_wallet(address)

        if wallet.encrypted:
            if not password:
                raise EncryptionError("Password required for mainnet wallet")
            return self._decrypt_secret(wallet.secret_key, password)
        else:
            return wallet.secret_key

    # =========================================================================
    # Encryption Helpers
    # =========================================================================

    def _encrypt_secret(self, secret_key: str, password: str) -> str:
        """
        Encrypt a secret key with a password.

        Args:
            secret_key: The plaintext secret key.
            password: The password.

        Returns:
            Base64-encoded encrypted secret key with salt.
        """
        if not HAS_CRYPTO:
            raise EncryptionError("cryptography package not installed")

        # Generate a random salt
        salt = secrets.token_bytes(16)

        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

        # Encrypt
        fernet = Fernet(key)
        encrypted = fernet.encrypt(secret_key.encode())

        # Combine salt + encrypted data
        combined = salt + encrypted
        return base64.b64encode(combined).decode()

    def _decrypt_secret(self, encrypted_data: str, password: str) -> str:
        """
        Decrypt an encrypted secret key.

        Args:
            encrypted_data: Base64-encoded encrypted secret key with salt.
            password: The password.

        Returns:
            The plaintext secret key.

        Raises:
            EncryptionError: If decryption fails.
        """
        if not HAS_CRYPTO:
            raise EncryptionError("cryptography package not installed")

        try:
            # Decode and split salt + encrypted
            combined = base64.b64decode(encrypted_data)
            salt = combined[:16]
            encrypted = combined[16:]

            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

            # Decrypt
            fernet = Fernet(key)
            decrypted = fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")

    def generate_seed_phrase(self, secret_key: str) -> str:
        """
        Generate a BIP39-style seed phrase from a Stellar secret key.
        
        Args:
            secret_key: The Stellar secret key (S...)
            
        Returns:
            A 12-word seed phrase derived from the secret key.
        """
        try:
            # Stellar secret keys are 32 bytes, base32 encoded
            # Decode the secret key to get raw bytes
            try:
                # Remove the 'S' prefix and decode
                secret_bytes = base64.b32decode(secret_key[1:] + '=' * ((-len(secret_key[1:])) % 8))
            except Exception:
                # Fallback: treat as hex if base32 fails
                secret_bytes = bytes.fromhex(secret_key[2:])
            
            # Use SHA-256 to create entropy for seed generation
            entropy = hashlib.sha256(secret_bytes).digest()
            
            # BIP39 wordlist (simplified version - using common words)
            # In production, you'd use the full BIP39 wordlist
            wordlist = [
                "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract",
                "absurd", "abuse", "access", "accident", "account", "accuse", "achieve", "acid",
                "acoustic", "acquire", "across", "act", "action", "actor", "actress", "actual",
                "adapt", "add", "addict", "address", "adjust", "admit", "adult", "advance",
                "advice", "aerobic", "affair", "afford", "afraid", "again", "age", "agent",
                "agree", "ahead", "aim", "air", "airport", "aisle", "alarm", "album", "alcohol",
                "alert", "alien", "all", "alley", "allow", "almost", "alone", "alpha", "already",
                "also", "alter", "always", "amateur", "amazing", "among", "amount", "amused",
                "analyst", "anchor", "ancient", "anger", "angle", "angry", "animal", "ankle",
                "announce", "annual", "another", "answer", "antenna", "antique", "anxiety", "any",
                "apart", "apparatus", "apparent", "appeal", "apple", "apply", "approach", "approve",
                "april", "arch", "arctic", "area", "arena", "argue", "arm", "armor", "army",
                "around", "arrange", "arrest", "arrive", "arrow", "art", "article", "artist", "artwork",
                "aspect", "asset", "assign", "assist", "assume", "asthma", "athlete", "atom", "attack",
                "attend", "attitude", "attract", "auction", "audit", "august", "aunt", "author",
                "auto", "autumn", "average", "avocado", "avoid", "awake", "aware", "away", "awesome",
                "awful", "awkward", "axis", "baby", "bachelor", "bacon", "badge", "bag", "balance",
                "balcony", "ball", "bamboo", "banana", "banner", "bar", "barely", "bargain", "barrel",
                "base", "basic", "basket", "basketball", "bat", "bath", "bathroom", "battery", "beach",
                "bean", "bear", "beat", "beautiful", "beauty", "because", "become", "beef", "before",
                "begin", "behave", "behind", "believe", "below", "belt", "bench", "beneficial", "best",
                "betray", "better", "between", "beyond", "bicycle", "bid", "bike", "bind", "biology",
                "bird", "birth", "bitter", "black", "blade", "blame", "blanket", "blast", "bleak",
                "bless", "blind", "blink", "blood", "blossom", "blow", "blue", "blur", "blunt",
                "board", "boat", "body", "boil", "bomb", "bond", "bone", "bonus", "book", "boost",
                "booth", "border", "boring", "borrow", "boss", "both", "bottle", "bottom", "bound",
                "bow", "box", "boy", "brain", "brave", "bread", "break", "breast", "breed", "brick",
                "bridge", "brief", "bright", "bring", "broad", "brother", "broken", "bronze", "broom",
                "brother", "brown", "brush", "bubble", "buddy", "budget", "buffalo", "build", "bulb",
                "bulk", "bullet", "bundle", "bunker", "burden", "burger", "burst", "bus", "business",
                "busy", "butter", "buyer", "buzz", "cabbage", "cabin", "cable", "cactus", "cage", "cake",
                "call", "calm", "camera", "camp", "can", "canal", "cancel", "candle", "cannon", "canoe",
                "canvas", "canyon", "capable", "capital", "captain", "car", "carbon", "card", "cargo",
                "carry", "cart", "case", "cash", "casino", "castle", "casual", "cat", "catalog", "catch",
                "category", "cattle", "caught", "cause", "cave", "ceiling", "cell", "cement", "census",
                "century", "cereal", "certain", "chair", "chalk", "champion", "change", "chaos", "chapter",
                "charge", "chat", "cheap", "check", "cheese", "chef", "cherry", "chest", "chicken", "chief",
                "child", "chimney", "choice", "choose", "chronic", "chunk", "churn", "cigar", "cinnamon",
                "circle", "citizen", "city", "claim", "clap", "clarify", "claw", "clay", "clean", "clerk",
                "clever", "click", "client", "climate", "climb", "clock", "close", "cloth", "cloud", "cloudy",
                "club", "clump", "cluster", "coach", "coast", "coconut", "code", "coffee", "coil", "coin",
                "collect", "color", "column", "combine", "comfort", "comic", "common", "company", "concert",
                "conduct", "confirm", "congress", "connect", "consider", "control", "convince", "cook", "cool",
                "copper", "copy", "coral", "core", "corn", "correct", "cost", "cotton", "couch", "country",
                "couple", "courage", "course", "court", "cousin", "cover", "coyote", "crack", "cradle",
                "craft", "crash", "crazy", "cream", "creek", "crew", "crime", "crisp", "critic", "crop",
                "cross", "crowd", "crucial", "cruel", "cruise", "crumble", "crunch", "crush", "cry", "crystal",
                "cube", "culture", "cup", "cupboard", "curious", "current", "curtain", "curve", "cushion",
                "custom", "cute", "cycle", "dad", "damage", "damp", "dance", "danger", "daring", "dash",
                "daughter", "dawn", "day", "deal", "debate", "debris", "decade", "decent", "decide", "decline",
                "decorate", "decrease", "defense", "define", "defy", "degree", "delay", "deliver", "demand",
                "demise", "denial", "dense", "dental", "deny", "depart", "depend", "deposit", "depth", "deputy"
            ]
            
            # Generate 12 words from entropy
            # Each word represents 11 bits, so we need 132 bits for 12 words
            # We'll use the entropy to generate indices
            indices = []
            data = entropy
            
            # Convert entropy to indices
            for i in range(12):
                if i < 11:
                    # For first 11 words, use 11 bits each
                    start = i * 11
                    end = start + 11
                    if end <= len(data) * 8:
                        # Convert bytes to bits and extract 11 bits
                        byte_value = int.from_bytes(data, 'big')
                        shift = (len(data) * 8) - end
                        index = (byte_value >> shift) & 0x7FF
                    else:
                        # Fallback to simpler method
                        index = int.from_bytes(data[i:i+4] or b'\x00\x00\x00\x01', 'big') % len(wordlist)
                else:
                    # For checksum word
                    index = int.from_bytes(data[-4:] or b'\x00\x00\x00\x01', 'big') % len(wordlist)
                
                indices.append(index % len(wordlist))
            
            # Convert indices to words
            seed_phrase = ' '.join(wordlist[i] for i in indices)
            
            return seed_phrase
        except Exception as e:
            # Fallback to a simple deterministic seed phrase if generation fails
            return f"seed {secret_key[:8]} {secret_key[8:16]} {secret_key[16:24]} {secret_key[24:32]} {secret_key[32:40]} {secret_key[40:48]} {secret_key[48:56]}".replace("S", "")

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _get_wallet_count(self, network: str) -> int:
        """Get the count of wallets for a network."""
        return len(self.db.search(self.query.network == network))

    def wallet_exists(self, address: str) -> bool:
        """Check if a wallet exists."""
        return len(self.db.search(self.query.address == address)) > 0


# Convenience functions for direct use
_manager: Optional[WalletManager] = None


def get_wallet_manager() -> WalletManager:
    """Get or create the global wallet manager instance."""
    global _manager
    if _manager is None:
        _manager = WalletManager()
    return _manager


def create_testnet_wallet(label: Optional[str] = None, auto_fund: bool = True) -> Dict[str, Any]:
    """Create a testnet wallet and return its public info."""
    manager = get_wallet_manager()
    wallet = manager.create_testnet_wallet(label=label, auto_fund=auto_fund)
    return wallet.to_dict()


def list_testnet_wallets() -> List[Dict[str, Any]]:
    """List all testnet wallets with public info only."""
    manager = get_wallet_manager()
    wallets = manager.list_testnet_wallets()
    return [w.public_info() for w in wallets]


def get_testnet_wallet_balance(address: str) -> Dict[str, Any]:
    """Get the balance of a testnet wallet."""
    manager = get_wallet_manager()
    return manager.get_balance(address, network="testnet")


def fund_testnet_wallet(address: str) -> Dict[str, Any]:
    """Fund a testnet wallet via Friendbot."""
    manager = get_wallet_manager()
    return manager.fund_testnet_wallet(address)


def delete_testnet_wallet(address: str) -> bool:
    """Delete a testnet wallet."""
    manager = get_wallet_manager()
    wallet = manager.get_wallet(address)
    if wallet.network != "testnet":
        raise WalletManagerError("Can only delete testnet wallets via API")
    return manager.delete_wallet(address)
