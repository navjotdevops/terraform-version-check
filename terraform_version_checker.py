#!/usr/bin/env python3
"""
Terraform Version Checker GitHub Action
Checks .terraform-version files and required_version constraints in Terraform files
and suggests upgrades to the latest stable Terraform version.
"""

import os
import re
import sys
import json
import glob
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from packaging import version
import requests


class TerraformVersionChecker:
    """Check Terraform versions and suggest upgrades."""
    
    def __init__(self, directory: str = "/", github_token: Optional[str] = None):
        self.directory = directory
        self.github_token = github_token
        self.latest_version = None
        self.findings = []
        
    def get_latest_terraform_version(self) -> str:
        """Fetch the latest Terraform version from HashiCorp releases."""
        try:
            # Use HashiCorp's releases API
            url = "https://api.releases.hashicorp.com/v1/releases/terraform"
            params = {
                "license_class": "oss",
                "limit": "50"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            releases = response.json()
            
            # Filter stable versions (no -alpha, -beta, -rc)
            stable_versions = []
            for release in releases:
                ver = release.get("version", "")
                if ver and not any(tag in ver for tag in ["-alpha", "-beta", "-rc"]):
                    try:
                        stable_versions.append(version.parse(ver))
                    except Exception:
                        continue
            
            if stable_versions:
                latest = max(stable_versions)
                self.latest_version = str(latest)
                return self.latest_version
            
            # Fallback
            return "1.10.0"
            
        except Exception as e:
            print(f"⚠️  Warning: Could not fetch latest Terraform version: {e}")
            print("Using fallback version 1.10.0")
            self.latest_version = "1.10.0"
            return self.latest_version
    
    def parse_version_constraint(self, constraint: str) -> Optional[str]:
        """Parse Terraform version constraint and extract version number."""
        # Remove whitespace
        constraint = constraint.strip()
        
        # Match patterns like:
        # >= 1.0.0
        # ~> 1.0
        # = 1.0.0
        # 1.0.0
        patterns = [
            r'[>=<~!]*\s*(\d+\.\d+(?:\.\d+)?)',  # With operators
            r'^(\d+\.\d+(?:\.\d+)?)$',  # Just version
        ]
        
        for pattern in patterns:
            match = re.search(pattern, constraint)
            if match:
                return match.group(1)
        
        return None
    
    def check_terraform_version_file(self, file_path: Path) -> Optional[Dict]:
        """Check .terraform-version file."""
        try:
            with open(file_path, 'r') as f:
                current_version = f.read().strip()
            
            # Parse version
            parsed_version = self.parse_version_constraint(current_version)
            if not parsed_version:
                return None
            
            # Compare with latest
            try:
                current = version.parse(parsed_version)
                latest = version.parse(self.latest_version)
                
                if current < latest:
                    return {
                        "type": "terraform-version-file",
                        "file": str(file_path),
                        "current_version": parsed_version,
                        "latest_version": self.latest_version,
                        "needs_update": True
                    }
            except Exception as e:
                print(f"⚠️  Warning: Could not parse version in {file_path}: {e}")
                
        except Exception as e:
            print(f"⚠️  Warning: Could not read {file_path}: {e}")
        
        return None
    
    def check_required_version(self, file_path: Path) -> List[Dict]:
        """Check required_version in Terraform files."""
        findings = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Match terraform block with required_version
            # Handles both simple and complex patterns
            pattern = r'terraform\s*{[^}]*required_version\s*=\s*"([^"]+)"'
            matches = re.finditer(pattern, content, re.DOTALL)
            
            for match in matches:
                constraint = match.group(1)
                parsed_version = self.parse_version_constraint(constraint)
                
                if not parsed_version:
                    continue
                
                try:
                    current = version.parse(parsed_version)
                    latest = version.parse(self.latest_version)
                    
                    if current < latest:
                        findings.append({
                            "type": "required-version",
                            "file": str(file_path),
                            "current_constraint": constraint,
                            "current_version": parsed_version,
                            "latest_version": self.latest_version,
                            "needs_update": True,
                            "suggested_constraint": f">= {self.latest_version}"
                        })
                except Exception as e:
                    print(f"⚠️  Warning: Could not parse version in {file_path}: {e}")
                    
        except Exception as e:
            print(f"⚠️  Warning: Could not read {file_path}: {e}")
        
        return findings
    
    def scan_directory(self, base_path: str):
        """Scan directory for Terraform version files and configurations."""
        base_path = Path(base_path).resolve()
        
        if not base_path.exists():
            print(f"❌ Error: Directory {base_path} does not exist")
            return
        
        print(f"🔍 Scanning directory: {base_path}")
        
        # Check .terraform-version files
        version_files = list(base_path.glob("**/.terraform-version"))
        for version_file in version_files:
            finding = self.check_terraform_version_file(version_file)
            if finding:
                self.findings.append(finding)
        
        # Check .tf files for required_version
        tf_files = list(base_path.glob("**/*.tf"))
        for tf_file in tf_files:
            findings = self.check_required_version(tf_file)
            self.findings.extend(findings)
    
    def generate_report(self) -> str:
        """Generate a summary report."""
        if not self.findings:
            return "✅ All Terraform versions are up to date!"
        
        report = []
        report.append(f"\n📦 Terraform Version Check Report")
        report.append(f"Latest stable version: {self.latest_version}")
        report.append(f"\n{'='*80}\n")
        
        # Group by file
        files_with_updates = {}
        for finding in self.findings:
            file_path = finding["file"]
            if file_path not in files_with_updates:
                files_with_updates[file_path] = []
            files_with_updates[file_path].append(finding)
        
        for file_path, findings in files_with_updates.items():
            report.append(f"\n📄 File: {file_path}")
            
            for finding in findings:
                if finding["type"] == "terraform-version-file":
                    report.append(f"  • .terraform-version file")
                    report.append(f"    Current: {finding['current_version']}")
                    report.append(f"    Latest:  {finding['latest_version']}")
                    report.append(f"    ⚠️  Update recommended")
                    
                elif finding["type"] == "required-version":
                    report.append(f"  • required_version constraint")
                    report.append(f"    Current: {finding['current_constraint']}")
                    report.append(f"    Version: {finding['current_version']}")
                    report.append(f"    Latest:  {finding['latest_version']}")
                    report.append(f"    Suggested: {finding['suggested_constraint']}")
                    report.append(f"    ⚠️  Update recommended")
        
        report.append(f"\n{'='*80}")
        report.append(f"\n📊 Summary: {len(self.findings)} update(s) recommended")
        
        return "\n".join(report)
    
    def generate_github_output(self) -> Dict:
        """Generate GitHub Actions output format."""
        return {
            "updates_found": len(self.findings) > 0,
            "update_count": len(self.findings),
            "latest_version": self.latest_version,
            "findings": self.findings
        }
    
    def set_github_output(self):
        """Set GitHub Actions outputs."""
        output = self.generate_github_output()
        
        # Set output using environment file (new method)
        github_output = os.getenv("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                f.write(f"updates_found={str(output['updates_found']).lower()}\n")
                f.write(f"update_count={output['update_count']}\n")
                f.write(f"latest_version={output['latest_version']}\n")
                f.write(f"findings={json.dumps(output['findings'])}\n")
        
        # Also print for visibility
        print(f"\n::set-output name=updates_found::{str(output['updates_found']).lower()}")
        print(f"::set-output name=update_count::{output['update_count']}")
        print(f"::set-output name=latest_version::{output['latest_version']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check Terraform versions and suggest upgrades"
    )
    parser.add_argument(
        "--directory",
        default=os.getenv("INPUT_DIRECTORY", "."),
        help="Directory to scan for Terraform files"
    )
    parser.add_argument(
        "--github-token",
        default=os.getenv("INPUT_TOKEN", os.getenv("GITHUB_TOKEN")),
        help="GitHub token for API access"
    )
    parser.add_argument(
        "--fail-on-updates",
        action="store_true",
        default=os.getenv("INPUT_FAIL_ON_UPDATES", "false").lower() == "true",
        help="Fail the action if updates are found"
    )
    
    args = parser.parse_args()
    
    # Support multiple directories separated by newlines
    directories = [d.strip() for d in args.directory.split("\n") if d.strip()]
    
    checker = TerraformVersionChecker(github_token=args.github_token)
    
    # Get latest version
    print(f"🔍 Fetching latest Terraform version...")
    latest = checker.get_latest_terraform_version()
    print(f"✅ Latest stable Terraform version: {latest}\n")
    
    # Scan each directory
    for directory in directories:
        checker.scan_directory(directory)
    
    # Generate and print report
    report = checker.generate_report()
    print(report)
    
    # Set GitHub Actions outputs
    if os.getenv("GITHUB_ACTIONS"):
        checker.set_github_output()
    
    # Exit with error if updates found and fail-on-updates is set
    if args.fail_on_updates and checker.findings:
        print(f"\n❌ Action failed: {len(checker.findings)} update(s) found")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
