"""
Soroban Contract Generator

Generates Stellar Soroban smart contracts from HEAVYMETA collection metadata.
Ports the ICP/Motoko contract generation system to Rust-based Soroban contracts.
"""

import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


def _get_template_dir() -> Path:
    """Get the template directory path, handling both development and frozen (PyInstaller) environments."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS)
    else:
        # Running in development
        base_path = Path(__file__).parent

    return base_path / "templates" / "soroban"


class SorobanGeneratorError(Exception):
    """Base exception for Soroban generator errors."""
    pass


class ValidationError(SorobanGeneratorError):
    """Raised when input validation fails."""
    pass


class TemplateError(SorobanGeneratorError):
    """Raised when template rendering fails."""
    pass


class SorobanGenerator:
    """
    Generates Stellar Soroban smart contracts from HEAVYMETA collection metadata.

    This class handles:
    - Input validation
    - Template data transformation
    - Jinja2 template rendering
    - Output file generation
    """

    # Valid property action types
    VALID_ACTION_TYPES = {'Static', 'Immutable', 'Incremental', 'Decremental', 'Bicremental', 'Setter'}

    # Valid NFT types
    VALID_NFT_TYPES = {'HVYC', 'HVYI', 'HVYA', 'HVYW', 'HVYO', 'HVYG', 'HVYAU'}

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the Soroban generator.

        Args:
            template_dir: Optional custom template directory path.
                         If not provided, uses the default templates/soroban/ directory.
        """
        self.template_dir = template_dir or _get_template_dir()

        if not self.template_dir.exists():
            raise TemplateError(f"Template directory not found: {self.template_dir}")

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Add custom filters
        self.env.filters['snake_case'] = self._to_snake_case
        self.env.filters['pascal_case'] = self._to_pascal_case
        self.env.filters['upper'] = str.upper
        self.env.filters['capitalize'] = str.capitalize

    def generate(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate all contract files from input data.

        Args:
            data: Contract configuration dictionary containing:
                - contract_name: Name of the contract/collection
                - symbol: Token symbol (e.g., "SWARS")
                - max_supply: Maximum NFT supply
                - nft_type: Optional NFT type (default: "HVYC")
                - val_props: Optional dictionary of value properties

        Returns:
            Dictionary mapping file paths to generated content:
                - "Cargo.toml": Cargo build configuration
                - "src/lib.rs": Main contract implementation
                - "src/types.rs": Type definitions
                - "src/storage.rs": Storage key definitions
                - "src/test.rs": Unit tests

        Raises:
            ValidationError: If input data is invalid
            TemplateError: If template rendering fails
        """
        self._validate(data)
        template_data = self._build_template_data(data)

        try:
            return {
                "Cargo.toml": self._render("Cargo.toml.j2", template_data),
                "src/lib.rs": self._render("lib.rs.j2", template_data),
                "src/types.rs": self._render("types.rs.j2", template_data),
                "src/storage.rs": self._render("storage.rs.j2", template_data),
                "src/test.rs": self._render("test.rs.j2", template_data),
            }
        except TemplateNotFound as e:
            raise TemplateError(f"Template not found: {e}")
        except Exception as e:
            raise TemplateError(f"Template rendering failed: {e}")

    def generate_types_only(self, data: Dict[str, Any]) -> str:
        """
        Generate only the types.rs file content.

        Args:
            data: Contract configuration dictionary

        Returns:
            Generated types.rs content
        """
        self._validate(data)
        template_data = self._build_template_data(data)
        return self._render("types.rs.j2", template_data)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate contract configuration without generating.

        Args:
            data: Contract configuration dictionary

        Returns:
            Dictionary with 'valid' boolean and 'errors' list
        """
        errors = []

        # Required fields
        required = ["contract_name", "symbol", "max_supply"]
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Validate contract_name
        if "contract_name" in data:
            name = data["contract_name"]
            if not name or not isinstance(name, str):
                errors.append("contract_name must be a non-empty string")
            elif not re.match(r'^[a-zA-Z][a-zA-Z0-9_\- ]*$', name):
                errors.append("contract_name must start with a letter and contain only letters, numbers, underscores, hyphens, and spaces")

        # Validate symbol
        if "symbol" in data:
            symbol = data["symbol"]
            if not symbol or not isinstance(symbol, str):
                errors.append("symbol must be a non-empty string")
            elif len(symbol) > 10:
                errors.append("symbol must be 10 characters or less")

        # Validate max_supply
        if "max_supply" in data:
            max_supply = data["max_supply"]
            if not isinstance(max_supply, int) or max_supply <= 0:
                errors.append("max_supply must be a positive integer")

        # Validate nft_type if provided
        if "nft_type" in data and data["nft_type"]:
            if data["nft_type"] not in self.VALID_NFT_TYPES:
                errors.append(f"Invalid nft_type: {data['nft_type']}. Valid types: {', '.join(self.VALID_NFT_TYPES)}")

        # Validate val_props
        if "val_props" in data and data["val_props"]:
            val_props = data["val_props"]
            if not isinstance(val_props, dict):
                errors.append("val_props must be a dictionary")
            else:
                for prop_name, prop_config in val_props.items():
                    prop_errors = self._validate_val_prop(prop_name, prop_config)
                    errors.extend(prop_errors)

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def list_templates(self) -> List[Dict[str, str]]:
        """
        List available templates and their descriptions.

        Returns:
            List of template information dictionaries
        """
        return [
            {"name": "lib.rs.j2", "description": "Main contract implementation with NFT core and value property functions"},
            {"name": "types.rs.j2", "description": "Type definitions, error enums, and property constants"},
            {"name": "storage.rs.j2", "description": "Storage key definitions for persistent and instance data"},
            {"name": "Cargo.toml.j2", "description": "Cargo build configuration for Soroban contract"},
            {"name": "test.rs.j2", "description": "Unit test scaffolding for contract functions"},
        ]

    def _validate(self, data: Dict[str, Any]) -> None:
        """
        Validate input data and raise ValidationError if invalid.

        Args:
            data: Contract configuration dictionary

        Raises:
            ValidationError: If validation fails
        """
        result = self.validate(data)
        if not result["valid"]:
            raise ValidationError("; ".join(result["errors"]))

    def _validate_val_prop(self, name: str, config: Dict[str, Any]) -> List[str]:
        """
        Validate a single value property configuration.

        Args:
            name: Property name
            config: Property configuration dictionary

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Validate property name
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
            errors.append(f"Property name '{name}' must start with a letter and contain only letters, numbers, and underscores")

        if not isinstance(config, dict):
            errors.append(f"Property '{name}' configuration must be a dictionary")
            return errors

        # Check for required fields
        required_fields = ["default", "min", "max"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Property '{name}' missing required field: {field}")

        # Validate numeric fields
        for field in ["default", "min", "max", "amount"]:
            if field in config and not isinstance(config[field], (int, float)):
                errors.append(f"Property '{name}' field '{field}' must be a number")

        # Validate min <= default <= max
        if all(field in config for field in ["default", "min", "max"]):
            if config["min"] > config["max"]:
                errors.append(f"Property '{name}': min ({config['min']}) cannot be greater than max ({config['max']})")
            if config["default"] < config["min"] or config["default"] > config["max"]:
                errors.append(f"Property '{name}': default ({config['default']}) must be between min ({config['min']}) and max ({config['max']})")

        # Validate prop_action_type
        action_type = config.get("prop_action_type", "Setter")
        if action_type not in self.VALID_ACTION_TYPES:
            errors.append(f"Property '{name}' has invalid prop_action_type: {action_type}. Valid types: {', '.join(self.VALID_ACTION_TYPES)}")

        # Validate amount for cremental types
        if action_type in ("Incremental", "Decremental", "Bicremental"):
            if "amount" not in config or config["amount"] <= 0:
                errors.append(f"Property '{name}' with action type '{action_type}' requires a positive 'amount' field")

        return errors

    def _build_template_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform API input to template data structure.

        Args:
            data: Raw input data from API

        Returns:
            Transformed data ready for template rendering
        """
        contract_name = data["contract_name"]

        # Filter val_props: exclude Static and immutable properties
        # (Static properties have no contract functions, immutable can only be read)
        val_props = {}
        for name, prop in data.get("val_props", {}).items():
            action_type = prop.get("prop_action_type", "Setter")
            is_immutable = prop.get("immutable", False)

            # Skip Static properties (they have no contract functions)
            if action_type == "Static":
                continue

            # Include the property with computed value_type
            val_props[name] = {
                "default": int(prop.get("default", 0)),
                "min": int(prop.get("min", 0)),
                "max": int(prop.get("max", 100)),
                "amount": int(prop.get("amount", 1)),
                "prop_action_type": action_type,
                "immutable": is_immutable,
                "value_type": self._get_rust_type(prop),
            }

        return {
            "contract": {
                "name": self._to_pascal_case(contract_name),
                "name_snake": self._to_snake_case(contract_name),
                "symbol": data["symbol"],
                "max_supply": data["max_supply"],
                "nft_type": data.get("nft_type", "HVYC"),
            },
            "val_props": val_props,
        }

    def _render(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        Render a template with the given data.

        Args:
            template_name: Name of the template file
            data: Data to pass to the template

        Returns:
            Rendered template content
        """
        template = self.env.get_template(template_name)
        return template.render(**data)

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """
        Convert a string to snake_case.

        Examples:
            "SpaceWarriors" -> "space_warriors"
            "space-warriors" -> "space_warriors"
            "Space Warriors" -> "space_warriors"
        """
        # Replace hyphens and spaces with underscores
        name = name.replace('-', '_').replace(' ', '_')
        # Insert underscore before uppercase letters and convert to lowercase
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        # Remove duplicate underscores and convert to lowercase
        return re.sub('_+', '_', s2).lower().strip('_')

    @staticmethod
    def _to_pascal_case(name: str) -> str:
        """
        Convert a string to PascalCase.

        Examples:
            "space_warriors" -> "SpaceWarriors"
            "space-warriors" -> "SpaceWarriors"
            "Space Warriors" -> "SpaceWarriors"
        """
        # Split on underscores, hyphens, and spaces
        words = re.split(r'[-_\s]+', name)
        return ''.join(word.capitalize() for word in words if word)

    @staticmethod
    def _get_rust_type(prop: Dict[str, Any]) -> str:
        """
        Determine the appropriate Rust type for a property.

        Currently defaults to u64 for all integer properties.
        Could be extended to support other types (i64, u128, i128) based on value range.

        Args:
            prop: Property configuration dictionary

        Returns:
            Rust type string (e.g., "u64")
        """
        # Check if max value requires larger type
        max_val = prop.get("max", 0)

        # u64 max is 18,446,744,073,709,551,615
        # If values could be larger or negative, could extend this
        if max_val > 2**63 - 1:
            return "u128"

        # Default to u64 for unsigned integer values
        return "u64"


# Convenience function for direct use
def generate_soroban_contract(data: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate a complete Soroban contract from collection metadata.

    This is a convenience function that creates a SorobanGenerator instance
    and generates all contract files.

    Args:
        data: Contract configuration dictionary containing:
            - contract_name: Name of the contract/collection
            - symbol: Token symbol
            - max_supply: Maximum NFT supply
            - nft_type: Optional NFT type (default: "HVYC")
            - val_props: Optional dictionary of value properties

    Returns:
        Dictionary mapping file paths to generated content

    Raises:
        ValidationError: If input data is invalid
        TemplateError: If template rendering fails
    """
    generator = SorobanGenerator()
    return generator.generate(data)
