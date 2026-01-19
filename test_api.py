#!/usr/bin/env python3
"""
HEAVYMETADATA API Test Suite

Tests all API endpoints for consistency and accuracy.
Compares API output with hvym CLI output where applicable.

Usage:
    python test_api.py [--cli-path PATH] [--api-url URL] [--verbose]

Requirements:
    - API server must be running (or use --start-server flag)
    - hvym CLI must be installed for comparison tests
"""

import argparse
import json
import subprocess
import sys
import time
import requests
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from pathlib import Path

# Default paths and URLs
DEFAULT_CLI_PATH = r"C:\Users\surfa\AppData\Local\heavymeta-cli\hvym-windows.exe"
DEFAULT_API_URL = "http://127.0.0.1:7777"


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    message: str
    api_response: Optional[Dict] = None
    cli_response: Optional[Dict] = None
    diff: Optional[str] = None


class APITester:
    """Test runner for HEAVYMETADATA API."""

    def __init__(self, api_url: str, cli_path: str, verbose: bool = False):
        self.api_url = api_url.rstrip('/')
        self.cli_path = cli_path
        self.verbose = verbose
        self.results: List[TestResult] = []

    def log(self, msg: str):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"  [DEBUG] {msg}")

    def run_cli_command(self, *args) -> Tuple[bool, str]:
        """Run hvym CLI command and return (success, output)."""
        try:
            cmd = [self.cli_path] + list(args)
            self.log(f"Running CLI: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
        except FileNotFoundError:
            return False, f"CLI not found at {self.cli_path}"
        except subprocess.TimeoutExpired:
            return False, "CLI command timed out"
        except Exception as e:
            return False, str(e)

    def api_get(self, endpoint: str) -> Tuple[bool, Dict]:
        """Make GET request to API endpoint."""
        try:
            url = f"{self.api_url}{endpoint}"
            self.log(f"GET {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return True, response.json()
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def api_post(self, endpoint: str, data: Dict) -> Tuple[bool, Dict]:
        """Make POST request to API endpoint."""
        try:
            url = f"{self.api_url}{endpoint}"
            self.log(f"POST {url} with {json.dumps(data)[:100]}...")
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            return True, response.json()
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def compare_json(self, api_data: Dict, cli_data: Dict, ignore_keys: List[str] = None) -> Tuple[bool, str]:
        """Compare two JSON objects, return (match, diff_description)."""
        ignore_keys = ignore_keys or []

        def normalize(obj):
            """Normalize JSON for comparison (sort keys, handle floats)."""
            if isinstance(obj, dict):
                return {k: normalize(v) for k, v in sorted(obj.items()) if k not in ignore_keys}
            elif isinstance(obj, list):
                return [normalize(item) for item in obj]
            elif isinstance(obj, float):
                return round(obj, 6)
            return obj

        norm_api = normalize(api_data)
        norm_cli = normalize(cli_data)

        if norm_api == norm_cli:
            return True, "Match"
        else:
            # Find differences
            diffs = []
            all_keys = set(list(norm_api.keys()) + list(norm_cli.keys()))
            for key in all_keys:
                api_val = norm_api.get(key, '<missing>')
                cli_val = norm_cli.get(key, '<missing>')
                if api_val != cli_val:
                    diffs.append(f"  {key}: API={api_val} vs CLI={cli_val}")
            return False, "\n".join(diffs[:10])  # Limit diff output

    def add_result(self, result: TestResult):
        """Add test result to results list."""
        self.results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"  [{status}] {result.name}: {result.message}")
        if not result.passed and result.diff:
            print(f"    Diff:\n{result.diff}")

    # =========================================================================
    # Health & Status Tests
    # =========================================================================

    def test_health(self):
        """Test /api/v1/health endpoint."""
        success, data = self.api_get("/api/v1/health")
        if success and data.get("status") == "running":
            self.add_result(TestResult("health", True, "API is healthy", data))
        else:
            self.add_result(TestResult("health", False, f"Health check failed: {data}", data))

    def test_status(self):
        """Test /api/v1/status endpoint."""
        success, data = self.api_get("/api/v1/status")
        if success and "endpoints" in data:
            endpoint_count = sum(
                len(v) if isinstance(v, dict) else 1
                for v in data["endpoints"].values()
            )
            self.add_result(TestResult("status", True, f"Status OK, {endpoint_count} endpoints listed", data))
        else:
            self.add_result(TestResult("status", False, f"Status check failed: {data}", data))

    # =========================================================================
    # Value Property Tests
    # =========================================================================

    def test_property_int(self):
        """Test /api/v1/property/int endpoint."""
        test_data = {
            "widget_type": "INT",
            "show": True,
            "prop_slider_type": "RANGE",
            "prop_action_type": "Setter",
            "default": 50,
            "min": 0,
            "max": 100,
            "immutable": False
        }
        success, api_data = self.api_post("/api/v1/property/int", test_data)

        if not success:
            self.add_result(TestResult("property/int", False, f"API request failed: {api_data}"))
            return

        # Validate structure
        required_keys = ["widget_type", "show", "prop_slider_type", "prop_action_type", "default", "min", "max"]
        missing = [k for k in required_keys if k not in api_data]
        if missing:
            self.add_result(TestResult("property/int", False, f"Missing keys: {missing}", api_data))
        else:
            self.add_result(TestResult("property/int", True, "Int property structure valid", api_data))

    def test_property_int_vs_cli(self):
        """Test /api/v1/property/int matches CLI slider-int-data."""
        # API request
        test_data = {
            "widget_type": "RANGE",
            "show": True,
            "prop_slider_type": "RANGE",
            "prop_action_type": "Setter",
            "default": 50,
            "min": 0,
            "max": 100,
            "immutable": False
        }
        api_success, api_data = self.api_post("/api/v1/property/int", test_data)

        # CLI command: slider-int-data default min max prop_slider_type prop_action_type widget_type show
        cli_success, cli_output = self.run_cli_command(
            "slider-int-data", "50", "0", "100", "RANGE", "Setter", "RANGE", "True"
        )

        if not api_success:
            self.add_result(TestResult("property/int vs CLI", False, f"API failed: {api_data}"))
            return
        if not cli_success:
            self.add_result(TestResult("property/int vs CLI", False, f"CLI failed: {cli_output}"))
            return

        try:
            cli_data = json.loads(cli_output)
            match, diff = self.compare_json(api_data, cli_data)
            self.add_result(TestResult(
                "property/int vs CLI",
                match,
                "Matches CLI output" if match else "Differs from CLI",
                api_data, cli_data, diff if not match else None
            ))
        except json.JSONDecodeError as e:
            self.add_result(TestResult("property/int vs CLI", False, f"CLI output not valid JSON: {e}"))

    def test_property_float(self):
        """Test /api/v1/property/float endpoint."""
        test_data = {
            "widget_type": "FLOAT",
            "show": True,
            "prop_slider_type": "RANGE",
            "prop_action_type": "Setter",
            "default": 0.5,
            "min": 0.0,
            "max": 1.0,
            "immutable": False
        }
        success, api_data = self.api_post("/api/v1/property/float", test_data)

        if not success:
            self.add_result(TestResult("property/float", False, f"API request failed: {api_data}"))
            return

        required_keys = ["widget_type", "show", "prop_slider_type", "prop_action_type", "default", "min", "max"]
        missing = [k for k in required_keys if k not in api_data]
        if missing:
            self.add_result(TestResult("property/float", False, f"Missing keys: {missing}", api_data))
        else:
            self.add_result(TestResult("property/float", True, "Float property structure valid", api_data))

    def test_property_text(self):
        """Test /api/v1/property/text endpoint."""
        test_data = {
            "name": "test_text",
            "show": True,
            "immutable": False,
            "text": "Hello World",
            "widget_type": "TEXT"
        }
        success, api_data = self.api_post("/api/v1/property/text", test_data)

        if success and api_data.get("name") == "test_text" and api_data.get("text") == "Hello World":
            self.add_result(TestResult("property/text", True, "Text property structure valid", api_data))
        else:
            self.add_result(TestResult("property/text", False, f"Text property failed: {api_data}", api_data))

    def test_behavior(self):
        """Test /api/v1/behavior endpoint."""
        test_data = {
            "name": "test_behavior",
            "trait_type": "property",
            "values": "0,50,100",
            "use_method": True,
            "method": "updateValue",
            "behavior_type": "increment",
            "use_behavior": True
        }
        success, api_data = self.api_post("/api/v1/behavior", test_data)

        if success and api_data.get("name") == "test_behavior":
            self.add_result(TestResult("behavior", True, "Behavior structure valid", api_data))
        else:
            self.add_result(TestResult("behavior", False, f"Behavior failed: {api_data}", api_data))

    def test_call(self):
        """Test /api/v1/call endpoint."""
        test_data = {
            "name": "test_call",
            "call_param": "doSomething"
        }
        success, api_data = self.api_post("/api/v1/call", test_data)

        if success and api_data.get("name") == "test_call":
            self.add_result(TestResult("call", True, "Call property structure valid", api_data))
        else:
            self.add_result(TestResult("call", False, f"Call property failed: {api_data}", api_data))

    # =========================================================================
    # Single Value & Slider Tests
    # =========================================================================

    def test_single_int(self):
        """Test /api/v1/single/int endpoint."""
        test_data = {"name": "count", "default": 10, "min": 0, "max": 100}
        success, api_data = self.api_post("/api/v1/single/int", test_data)

        if success and api_data.get("name") == "count":
            self.add_result(TestResult("single/int", True, "Single int structure valid", api_data))
        else:
            self.add_result(TestResult("single/int", False, f"Single int failed: {api_data}", api_data))

    def test_single_int_vs_cli(self):
        """Test /api/v1/single/int matches CLI single-int-data."""
        test_data = {"name": "count", "default": 10, "min": 0, "max": 100}
        api_success, api_data = self.api_post("/api/v1/single/int", test_data)

        cli_success, cli_output = self.run_cli_command("single-int-data", "count", "10", "0", "100")

        if not api_success:
            self.add_result(TestResult("single/int vs CLI", False, f"API failed: {api_data}"))
            return
        if not cli_success:
            self.add_result(TestResult("single/int vs CLI", False, f"CLI failed: {cli_output}"))
            return

        try:
            cli_data = json.loads(cli_output)
            match, diff = self.compare_json(api_data, cli_data)
            self.add_result(TestResult(
                "single/int vs CLI", match,
                "Matches CLI output" if match else "Differs from CLI",
                api_data, cli_data, diff if not match else None
            ))
        except json.JSONDecodeError as e:
            self.add_result(TestResult("single/int vs CLI", False, f"CLI output not valid JSON: {e}"))

    def test_single_float(self):
        """Test /api/v1/single/float endpoint."""
        test_data = {"name": "opacity", "default": 0.5, "min": 0.0, "max": 1.0}
        success, api_data = self.api_post("/api/v1/single/float", test_data)

        if success and api_data.get("name") == "opacity":
            self.add_result(TestResult("single/float", True, "Single float structure valid", api_data))
        else:
            self.add_result(TestResult("single/float", False, f"Single float failed: {api_data}", api_data))

    def test_single_float_vs_cli(self):
        """Test /api/v1/single/float matches CLI single-float-data."""
        test_data = {"name": "opacity", "default": 0.5, "min": 0.0, "max": 1.0}
        api_success, api_data = self.api_post("/api/v1/single/float", test_data)

        cli_success, cli_output = self.run_cli_command("single-float-data", "opacity", "0.5", "0.0", "1.0")

        if not api_success:
            self.add_result(TestResult("single/float vs CLI", False, f"API failed: {api_data}"))
            return
        if not cli_success:
            self.add_result(TestResult("single/float vs CLI", False, f"CLI failed: {cli_output}"))
            return

        try:
            cli_data = json.loads(cli_output)
            match, diff = self.compare_json(api_data, cli_data)
            self.add_result(TestResult(
                "single/float vs CLI", match,
                "Matches CLI output" if match else "Differs from CLI",
                api_data, cli_data, diff if not match else None
            ))
        except json.JSONDecodeError as e:
            self.add_result(TestResult("single/float vs CLI", False, f"CLI output not valid JSON: {e}"))

    def test_slider(self):
        """Test /api/v1/slider endpoint."""
        test_data = {
            "widget_type": "SLIDER",
            "show": True,
            "prop_slider_type": "RANGE",
            "prop_action_type": "Setter"
        }
        success, api_data = self.api_post("/api/v1/slider", test_data)

        if success and "widget_type" in api_data:
            self.add_result(TestResult("slider", True, "Slider structure valid", api_data))
        else:
            self.add_result(TestResult("slider", False, f"Slider failed: {api_data}", api_data))

    def test_slider_vs_cli(self):
        """Test /api/v1/slider matches CLI slider-data."""
        test_data = {
            "widget_type": "SLIDER",
            "show": True,
            "prop_slider_type": "RANGE",
            "prop_action_type": "Setter"
        }
        api_success, api_data = self.api_post("/api/v1/slider", test_data)

        cli_success, cli_output = self.run_cli_command("slider-data", "RANGE", "Setter", "SLIDER", "True")

        if not api_success:
            self.add_result(TestResult("slider vs CLI", False, f"API failed: {api_data}"))
            return
        if not cli_success:
            self.add_result(TestResult("slider vs CLI", False, f"CLI failed: {cli_output}"))
            return

        try:
            cli_data = json.loads(cli_output)
            match, diff = self.compare_json(api_data, cli_data)
            self.add_result(TestResult(
                "slider vs CLI", match,
                "Matches CLI output" if match else "Differs from CLI",
                api_data, cli_data, diff if not match else None
            ))
        except json.JSONDecodeError as e:
            self.add_result(TestResult("slider vs CLI", False, f"CLI output not valid JSON: {e}"))

    # =========================================================================
    # Mesh & Node Tests
    # =========================================================================

    def test_mesh(self):
        """Test /api/v1/mesh endpoint."""
        test_data = {"widget_type": "TOGGLE", "show": True, "name": "body", "visible": True}
        success, api_data = self.api_post("/api/v1/mesh", test_data)

        if success and api_data.get("name") == "body":
            self.add_result(TestResult("mesh", True, "Mesh structure valid", api_data))
        else:
            self.add_result(TestResult("mesh", False, f"Mesh failed: {api_data}", api_data))

    def test_mesh_vs_cli(self):
        """Test /api/v1/mesh matches CLI mesh-data."""
        test_data = {"widget_type": "TOGGLE", "show": True, "name": "body", "visible": True}
        api_success, api_data = self.api_post("/api/v1/mesh", test_data)

        cli_success, cli_output = self.run_cli_command("mesh-data", "body", "True", "TOGGLE", "True")

        if not api_success:
            self.add_result(TestResult("mesh vs CLI", False, f"API failed: {api_data}"))
            return
        if not cli_success:
            self.add_result(TestResult("mesh vs CLI", False, f"CLI failed: {cli_output}"))
            return

        try:
            cli_data = json.loads(cli_output)
            match, diff = self.compare_json(api_data, cli_data)
            self.add_result(TestResult(
                "mesh vs CLI", match,
                "Matches CLI output" if match else "Differs from CLI",
                api_data, cli_data, diff if not match else None
            ))
        except json.JSONDecodeError as e:
            self.add_result(TestResult("mesh vs CLI", False, f"CLI output not valid JSON: {e}"))

    def test_single_mesh(self):
        """Test /api/v1/single/mesh endpoint."""
        test_data = {"name": "arm", "visible": True}
        success, api_data = self.api_post("/api/v1/single/mesh", test_data)

        if success and api_data.get("name") == "arm":
            self.add_result(TestResult("single/mesh", True, "Single mesh structure valid", api_data))
        else:
            self.add_result(TestResult("single/mesh", False, f"Single mesh failed: {api_data}", api_data))

    def test_mesh_set(self):
        """Test /api/v1/mesh-set endpoint."""
        test_data = {
            "widget_type": "SELECT",
            "show": True,
            "set": [{"name": "mesh1", "visible": True}, {"name": "mesh2", "visible": False}],
            "selected_index": 0
        }
        success, api_data = self.api_post("/api/v1/mesh-set", test_data)

        if success and "set" in api_data:
            self.add_result(TestResult("mesh-set", True, "Mesh set structure valid", api_data))
        else:
            self.add_result(TestResult("mesh-set", False, f"Mesh set failed: {api_data}", api_data))

    def test_morph_set(self):
        """Test /api/v1/morph-set endpoint."""
        test_data = {
            "widget_type": "SELECT",
            "show": True,
            "set": ["smile", "frown", "neutral"],
            "selected_index": 0,
            "model_ref": {"name": "face"}
        }
        success, api_data = self.api_post("/api/v1/morph-set", test_data)

        if success and "set" in api_data:
            self.add_result(TestResult("morph-set", True, "Morph set structure valid", api_data))
        else:
            self.add_result(TestResult("morph-set", False, f"Morph set failed: {api_data}", api_data))

    def test_node(self):
        """Test /api/v1/node endpoint."""
        test_data = {"name": "root_bone", "type": "BONE"}
        success, api_data = self.api_post("/api/v1/node", test_data)

        if success and api_data.get("name") == "root_bone":
            self.add_result(TestResult("node", True, "Node structure valid", api_data))
        else:
            self.add_result(TestResult("node", False, f"Node failed: {api_data}", api_data))

    def test_node_vs_cli(self):
        """Test /api/v1/node matches CLI single-node-data."""
        test_data = {"name": "root_bone", "type": "BONE"}
        api_success, api_data = self.api_post("/api/v1/node", test_data)

        cli_success, cli_output = self.run_cli_command("single-node-data", "root_bone", "BONE")

        if not api_success:
            self.add_result(TestResult("node vs CLI", False, f"API failed: {api_data}"))
            return
        if not cli_success:
            self.add_result(TestResult("node vs CLI", False, f"CLI failed: {cli_output}"))
            return

        try:
            cli_data = json.loads(cli_output)
            match, diff = self.compare_json(api_data, cli_data)
            self.add_result(TestResult(
                "node vs CLI", match,
                "Matches CLI output" if match else "Differs from CLI",
                api_data, cli_data, diff if not match else None
            ))
        except json.JSONDecodeError as e:
            self.add_result(TestResult("node vs CLI", False, f"CLI output not valid JSON: {e}"))

    # =========================================================================
    # Animation Tests
    # =========================================================================

    def test_animation(self):
        """Test /api/v1/animation endpoint."""
        test_data = {
            "widget_type": "TOGGLE",
            "show": True,
            "name": "walk",
            "loop": "LOOP",
            "start": 0,
            "end": 60,
            "blending": "NORMAL",
            "weight": 1.0,
            "play": False,
            "model_ref": {"name": "character"}
        }
        success, api_data = self.api_post("/api/v1/animation", test_data)

        if success and api_data.get("name") == "walk":
            self.add_result(TestResult("animation", True, "Animation structure valid", api_data))
        else:
            self.add_result(TestResult("animation", False, f"Animation failed: {api_data}", api_data))

    # =========================================================================
    # Material Tests
    # =========================================================================

    def test_material_basic(self):
        """Test /api/v1/material/basic endpoint."""
        test_data = {"color": "#FF0000"}
        success, api_data = self.api_post("/api/v1/material/basic", test_data)

        if success and api_data.get("color") == "#FF0000":
            self.add_result(TestResult("material/basic", True, "Basic material structure valid", api_data))
        else:
            self.add_result(TestResult("material/basic", False, f"Basic material failed: {api_data}", api_data))

    def test_material_basic_vs_cli(self):
        """Test /api/v1/material/basic matches CLI basic-material-data."""
        test_data = {"color": "#FF0000"}
        api_success, api_data = self.api_post("/api/v1/material/basic", test_data)

        cli_success, cli_output = self.run_cli_command("basic-material-data", "#FF0000")

        if not api_success:
            self.add_result(TestResult("material/basic vs CLI", False, f"API failed: {api_data}"))
            return
        if not cli_success:
            self.add_result(TestResult("material/basic vs CLI", False, f"CLI failed: {cli_output}"))
            return

        try:
            cli_data = json.loads(cli_output)
            match, diff = self.compare_json(api_data, cli_data)
            self.add_result(TestResult(
                "material/basic vs CLI", match,
                "Matches CLI output" if match else "Differs from CLI",
                api_data, cli_data, diff if not match else None
            ))
        except json.JSONDecodeError as e:
            self.add_result(TestResult("material/basic vs CLI", False, f"CLI output not valid JSON: {e}"))

    def test_material_lambert(self):
        """Test /api/v1/material/lambert endpoint."""
        test_data = {"color": "#00FF00"}
        success, api_data = self.api_post("/api/v1/material/lambert", test_data)

        if success and api_data.get("color") == "#00FF00":
            self.add_result(TestResult("material/lambert", True, "Lambert material structure valid", api_data))
        else:
            self.add_result(TestResult("material/lambert", False, f"Lambert material failed: {api_data}", api_data))

    def test_material_phong(self):
        """Test /api/v1/material/phong endpoint."""
        test_data = {"color": "#0000FF", "specular": "#FFFFFF", "shininess": 30.0}
        success, api_data = self.api_post("/api/v1/material/phong", test_data)

        if success and api_data.get("color") == "#0000FF":
            self.add_result(TestResult("material/phong", True, "Phong material structure valid", api_data))
        else:
            self.add_result(TestResult("material/phong", False, f"Phong material failed: {api_data}", api_data))

    def test_material_standard(self):
        """Test /api/v1/material/standard endpoint."""
        test_data = {"color": "#FFFFFF", "roughness": 0.5, "metalness": 0.0}
        success, api_data = self.api_post("/api/v1/material/standard", test_data)

        if success and api_data.get("roughness") == 0.5:
            self.add_result(TestResult("material/standard", True, "Standard material structure valid", api_data))
        else:
            self.add_result(TestResult("material/standard", False, f"Standard material failed: {api_data}", api_data))

    def test_material_standard_vs_cli(self):
        """Test /api/v1/material/standard matches CLI standard-material-data."""
        test_data = {"color": "#FFFFFF", "roughness": 0.5, "metalness": 0.0}
        api_success, api_data = self.api_post("/api/v1/material/standard", test_data)

        cli_success, cli_output = self.run_cli_command("standard-material-data", "#FFFFFF", "0.5", "0.0")

        if not api_success:
            self.add_result(TestResult("material/standard vs CLI", False, f"API failed: {api_data}"))
            return
        if not cli_success:
            self.add_result(TestResult("material/standard vs CLI", False, f"CLI failed: {cli_output}"))
            return

        try:
            cli_data = json.loads(cli_output)
            match, diff = self.compare_json(api_data, cli_data)
            self.add_result(TestResult(
                "material/standard vs CLI", match,
                "Matches CLI output" if match else "Differs from CLI",
                api_data, cli_data, diff if not match else None
            ))
        except json.JSONDecodeError as e:
            self.add_result(TestResult("material/standard vs CLI", False, f"CLI output not valid JSON: {e}"))

    def test_material_pbr(self):
        """Test /api/v1/material/pbr endpoint."""
        test_data = {"color": "#CCCCCC", "roughness": 0.3, "metalness": 0.8}
        success, api_data = self.api_post("/api/v1/material/pbr", test_data)

        if success and api_data.get("metalness") == 0.8:
            self.add_result(TestResult("material/pbr", True, "PBR material structure valid", api_data))
        else:
            self.add_result(TestResult("material/pbr", False, f"PBR material failed: {api_data}", api_data))

    def test_mat_prop(self):
        """Test /api/v1/mat-prop endpoint."""
        test_data = {
            "widget_type": "MULTI",
            "show": True,
            "name": "skin_material",
            "type": "STANDARD",
            "emissive": False,
            "reflective": False,
            "irridescent": False,
            "sheen": False,
            "mat_ref": {"name": "skin"},
            "save_data": {}
        }
        success, api_data = self.api_post("/api/v1/mat-prop", test_data)

        if success and api_data.get("name") == "skin_material":
            self.add_result(TestResult("mat-prop", True, "Mat prop structure valid", api_data))
        else:
            self.add_result(TestResult("mat-prop", False, f"Mat prop failed: {api_data}", api_data))

    def test_mat_set(self):
        """Test /api/v1/mat-set endpoint."""
        test_data = {
            "widget_type": "SELECT",
            "show": True,
            "set": ["mat1", "mat2", "mat3"],
            "mesh_set": ["body", "head"],
            "material_id": 0,
            "selected_index": 0
        }
        success, api_data = self.api_post("/api/v1/mat-set", test_data)

        if success and "set" in api_data:
            self.add_result(TestResult("mat-set", True, "Mat set structure valid", api_data))
        else:
            self.add_result(TestResult("mat-set", False, f"Mat set failed: {api_data}", api_data))

    # =========================================================================
    # UI Tests
    # =========================================================================

    def test_menu(self):
        """Test /api/v1/menu endpoint."""
        test_data = {
            "name": "main_menu",
            "primary_color": "#FFFFFF",
            "secondary_color": "#000000",
            "text_color": "#FFFFFF",
            "alignment": "CENTER"
        }
        success, api_data = self.api_post("/api/v1/menu", test_data)

        if success and api_data.get("name") == "main_menu":
            self.add_result(TestResult("menu", True, "Menu structure valid", api_data))
        else:
            self.add_result(TestResult("menu", False, f"Menu failed: {api_data}", api_data))

    def test_menu_vs_cli(self):
        """Test /api/v1/menu matches CLI menu-data."""
        test_data = {
            "name": "main_menu",
            "primary_color": "#FFFFFF",
            "secondary_color": "#000000",
            "text_color": "#FFFFFF",
            "alignment": "CENTER"
        }
        api_success, api_data = self.api_post("/api/v1/menu", test_data)

        cli_success, cli_output = self.run_cli_command(
            "menu-data", "main_menu", "#FFFFFF", "#000000", "#FFFFFF", "CENTER"
        )

        if not api_success:
            self.add_result(TestResult("menu vs CLI", False, f"API failed: {api_data}"))
            return
        if not cli_success:
            self.add_result(TestResult("menu vs CLI", False, f"CLI failed: {cli_output}"))
            return

        try:
            cli_data = json.loads(cli_output)
            match, diff = self.compare_json(api_data, cli_data)
            self.add_result(TestResult(
                "menu vs CLI", match,
                "Matches CLI output" if match else "Differs from CLI",
                api_data, cli_data, diff if not match else None
            ))
        except json.JSONDecodeError as e:
            self.add_result(TestResult("menu vs CLI", False, f"CLI output not valid JSON: {e}"))

    def test_action(self):
        """Test /api/v1/action endpoint."""
        test_data = {
            "anim_type": "animation",
            "set": ["walk", "run", "idle"],
            "interaction": "click",
            "sequence": "sequential",
            "additive": False
        }
        success, api_data = self.api_post("/api/v1/action", test_data)

        if success and "anim_type" in api_data:
            self.add_result(TestResult("action", True, "Action structure valid", api_data))
        else:
            self.add_result(TestResult("action", False, f"Action failed: {api_data}", api_data))

    def test_labels(self):
        """Test /api/v1/labels endpoint."""
        test_data = {
            "value_prop_label": "Properties",
            "text_prop_label": "Text",
            "call_prop_label": "Calls",
            "mesh_prop_label": "Meshes",
            "mat_prop_label": "Materials",
            "anim_prop_label": "Animations",
            "mesh_set_label": "Mesh Sets",
            "morph_set_label": "Morph Sets",
            "mat_set_label": "Material Sets"
        }
        success, api_data = self.api_post("/api/v1/labels", test_data)

        if success and api_data.get("value_prop_label") == "Properties":
            self.add_result(TestResult("labels", True, "Labels structure valid", api_data))
        else:
            self.add_result(TestResult("labels", False, f"Labels failed: {api_data}", api_data))

    # =========================================================================
    # Interactable Test
    # =========================================================================

    def test_interactable(self):
        """Test /api/v1/interactable endpoint."""
        test_data = {
            "interactable": True,
            "has_return": False,
            "interaction_type": "click",
            "selector_dir": "forward",
            "name": "button1",
            "call": "onClick",
            "default_text": "Click me",
            "text_scale": 1.0,
            "text_wrap": False,
            "param_type": "none",
            "slider_param_type": "RANGE",
            "toggle_param_type": "TOGGLE",
            "string_param": "",
            "int_param": 0,
            "float_default": 0.0,
            "float_min": 0.0,
            "float_max": 1.0,
            "int_default": 0,
            "int_min": 0,
            "int_max": 100,
            "toggle_state": False,
            "toggle_int": 0,
            "mesh_set": [],
            "behavior": {}
        }
        success, api_data = self.api_post("/api/v1/interactable", test_data)

        if success and api_data.get("name") == "button1":
            self.add_result(TestResult("interactable", True, "Interactable structure valid", api_data))
        else:
            self.add_result(TestResult("interactable", False, f"Interactable failed: {api_data}", api_data))

    # =========================================================================
    # Collection Test
    # =========================================================================

    def test_collection(self):
        """Test /api/v1/collection endpoint."""
        test_data = {
            "collectionName": "TestCollection",
            "collectionType": "multi",
            "valProps": {},
            "textValProps": {},
            "callProps": {},
            "meshProps": {},
            "meshSets": {},
            "morphSets": {},
            "animProps": {},
            "matProps": {},
            "materialSets": {},
            "menuData": {},
            "propLabelData": {},
            "nodes": {},
            "actionProps": {}
        }
        success, api_data = self.api_post("/api/v1/collection", test_data)

        if success and api_data.get("collectionName") == "TestCollection":
            self.add_result(TestResult("collection", True, "Collection structure valid", api_data))
        else:
            self.add_result(TestResult("collection", False, f"Collection failed: {api_data}", api_data))

    # =========================================================================
    # Parse Endpoints Tests
    # =========================================================================

    def test_parse_val_prop(self):
        """Test /api/v1/parse/val-prop endpoint."""
        test_data = {
            "prop_action_type": "Static",
            "prop_value_type": "Int",
            "prop_slider_type": "RANGE",
            "show": True,
            "prop_immutable": False,
            "int_default": 50,
            "int_min": 0,
            "int_max": 100,
            "int_amount": 1
        }
        success, api_data = self.api_post("/api/v1/parse/val-prop", test_data)

        if success and "default" in api_data:
            self.add_result(TestResult("parse/val-prop", True, "Parse val-prop structure valid", api_data))
        else:
            self.add_result(TestResult("parse/val-prop", False, f"Parse val-prop failed: {api_data}", api_data))

    def test_parse_behavior_val_prop(self):
        """Test /api/v1/parse/behavior-val-prop endpoint."""
        test_data = {
            "prop_action_type": "Incremental",
            "prop_value_type": "Int",
            "prop_slider_type": "RANGE",
            "show": True,
            "prop_immutable": False,
            "int_default": 0,
            "int_min": 0,
            "int_max": 100,
            "int_amount": 10,
            "behavior_set": [{"name": "test", "values": "1,2,3"}]
        }
        success, api_data = self.api_post("/api/v1/parse/behavior-val-prop", test_data)

        if success and "behaviors" in api_data:
            self.add_result(TestResult("parse/behavior-val-prop", True, "Parse behavior-val-prop structure valid", api_data))
        else:
            self.add_result(TestResult("parse/behavior-val-prop", False, f"Parse behavior-val-prop failed: {api_data}", api_data))

    def test_parse_interactables(self):
        """Test /api/v1/parse/interactables endpoint."""
        test_data = {
            "obj_data": {
                "button1": {
                    "name": "button1",
                    "hvym_interactable": True,
                    "hvym_mesh_interaction_type": "click",
                    "hvym_mesh_interaction_name": "clickHandler",
                    "hvym_mesh_interaction_call": "onClick",
                    "hvym_interactable_behavior": "NONE",
                    "children": [{"name": "mesh1", "type": "MESH"}]
                }
            }
        }
        success, api_data = self.api_post("/api/v1/parse/interactables", test_data)

        if success and "button1" in api_data:
            self.add_result(TestResult("parse/interactables", True, "Parse interactables structure valid", api_data))
        else:
            self.add_result(TestResult("parse/interactables", False, f"Parse interactables failed: {api_data}", api_data))

    # =========================================================================
    # Run All Tests
    # =========================================================================

    def run_all_tests(self):
        """Run all test methods."""
        print("=" * 70)
        print("HEAVYMETADATA API Test Suite")
        print("=" * 70)
        print(f"API URL: {self.api_url}")
        print(f"CLI Path: {self.cli_path}")
        print("=" * 70)

        # Health & Status
        print("\n[Health & Status]")
        self.test_health()
        self.test_status()

        # Value Properties
        print("\n[Value Properties]")
        self.test_property_int()
        self.test_property_int_vs_cli()
        self.test_property_float()
        self.test_property_text()
        self.test_behavior()
        self.test_call()

        # Single Value & Slider
        print("\n[Single Value & Slider]")
        self.test_single_int()
        self.test_single_int_vs_cli()
        self.test_single_float()
        self.test_single_float_vs_cli()
        self.test_slider()
        self.test_slider_vs_cli()

        # Mesh & Node
        print("\n[Mesh & Node]")
        self.test_mesh()
        self.test_mesh_vs_cli()
        self.test_single_mesh()
        self.test_mesh_set()
        self.test_morph_set()
        self.test_node()
        self.test_node_vs_cli()

        # Animation
        print("\n[Animation]")
        self.test_animation()

        # Materials
        print("\n[Materials]")
        self.test_material_basic()
        self.test_material_basic_vs_cli()
        self.test_material_lambert()
        self.test_material_phong()
        self.test_material_standard()
        self.test_material_standard_vs_cli()
        self.test_material_pbr()
        self.test_mat_prop()
        self.test_mat_set()

        # UI
        print("\n[UI]")
        self.test_menu()
        self.test_menu_vs_cli()
        self.test_action()
        self.test_labels()

        # Interactable
        print("\n[Interactable]")
        self.test_interactable()

        # Collection
        print("\n[Collection]")
        self.test_collection()

        # Parse Endpoints
        print("\n[Parse Endpoints]")
        self.test_parse_val_prop()
        self.test_parse_behavior_val_prop()
        self.test_parse_interactables()

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
        print(f"Pass Rate: {(passed/total*100):.1f}%" if total > 0 else "No tests run")

        if failed > 0:
            print("\nFailed Tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}: {r.message}")

        print("=" * 70)
        return failed == 0


def main():
    parser = argparse.ArgumentParser(description="HEAVYMETADATA API Test Suite")
    parser.add_argument("--cli-path", default=DEFAULT_CLI_PATH, help="Path to hvym CLI executable")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API server URL")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Check if API is running
    try:
        response = requests.get(f"{args.api_url}/api/v1/health", timeout=5)
        if response.status_code != 200:
            print(f"Warning: API health check returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to API at {args.api_url}")
        print("Please start the API server first:")
        print("  python api_server.py")
        sys.exit(1)

    # Run tests
    tester = APITester(args.api_url, args.cli_path, args.verbose)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
