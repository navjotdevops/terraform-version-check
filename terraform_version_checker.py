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
    
    def __init__(self, directory: str = "/", github_token: Optional[str] = None, patches_behind: int = 2):
        self.directory = directory
        self.github_token = github_token
        self.patches_behind = patches_behind
        self.latest_version = None
        self.findings = []
        self.current_versions = set()  # Track unique current versions found
        
    def get_latest_terraform_version(self, patches_behind: int = 2) -> str:
        """Fetch the latest Terraform version from HashiCorp releases.
        
        Args:
            patches_behind: Number of patch versions behind latest (default: 2)
        """
        try:
            # Use HashiCorp's releases API
            url = "https://api.releases.hashicorp.com/v1/releases/terraform"
            params = {
                "license_class": "oss",
                "limit": "100"  # Get more releases to ensure we have enough patches
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
                # Sort versions in descending order
                stable_versions.sort(reverse=True)
                latest = stable_versions[0]
                
                # Get the same major.minor but patches_behind versions back
                target_major_minor = f"{latest.major}.{latest.minor}"
                same_minor_versions = [
                    v for v in stable_versions 
                    if f"{v.major}.{v.minor}" == target_major_minor
                ]
                
                # Get version 'patches_behind' patches back
                if len(same_minor_versions) > patches_behind:
                    target_version = same_minor_versions[patches_behind]
                else:
                    # If not enough patches, use the oldest in this minor
                    target_version = same_minor_versions[-1] if same_minor_versions else latest
                
                self.latest_version = str(target_version)
                print(f"ℹ️  Targeting version {patches_behind} patch(es) behind latest: {self.latest_version}")
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
        
        # Strip leading 'v' if present (e.g., v1.5.0 -> 1.5.0)
        if constraint.startswith('v'):
            constraint = constraint[1:]
        
        # Match patterns like:
        # >= 1.0.0
        # ~> 1.0
        # = 1.0.0
        # 1.0.0
        # v1.0.0 (handled by strip above)
        patterns = [
            r'[>=<~!]*\s*(\d+\.\d+(?:\.\d+)?)',  # With operators
            r'^(\d+\.\d+(?:\.\d+)?)$',  # Just version
        ]
        
        for pattern in patterns:
            match = re.search(pattern, constraint)
            if match:
                res = match.group(1)
                # Ensure no leading 'v' in the middle of a constraint like '>= v1.0'
                if res.startswith('v'):
                    res = res[1:]
                return res
        
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
            
            # Always track found version
            self.current_versions.add(parsed_version)
            
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
            # More robust pattern that handles nested blocks inside terraform {}
            # by searching for required_version as a standalone assignment
            pattern = r'required_version\s*=\s*"([^"]+)"'
            matches = re.finditer(pattern, content)
            
            for match in matches:
                constraint = match.group(1)
                parsed_version = self.parse_version_constraint(constraint)
                
                if not parsed_version:
                    continue
                
                # Always track found version
                self.current_versions.add(parsed_version)
                
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
    
    def get_current_version_summary(self) -> str:
        """Get a summary of current versions found."""
        if not self.current_versions:
            return "unknown"
        if len(self.current_versions) == 1:
            return list(self.current_versions)[0]
        # Multiple versions found
        sorted_versions = sorted(self.current_versions, key=lambda x: version.parse(x))
        return f"{sorted_versions[0]} (and others)"
    
    def generate_github_output(self) -> Dict:
        """Generate GitHub Actions output format."""
        return {
            "updates_found": len(self.findings) > 0,
            "update_count": len(self.findings),
            "latest_version": self.latest_version,
            "current_version": self.get_current_version_summary(),
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
                f.write(f"current_version={output['current_version']}\n")
                f.write(f"findings={json.dumps(output['findings'])}\n")
        
        # Also print for visibility
        print(f"\n::set-output name=updates_found::{str(output['updates_found']).lower()}")
        print(f"::set-output name=update_count::{output['update_count']}")
        print(f"::set-output name=latest_version::{output['latest_version']}")
        print(f"::set-output name=current_version::{output['current_version']}")


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
    parser.add_argument(
        "--patches-behind",
        type=int,
        default=int(os.getenv("INPUT_PATCHES_BEHIND", "2")),
        help="Number of patch versions behind latest to target (default: 2)"
    )
    
    args = parser.parse_args()
    
    # Support multiple directories separated by newlines
    directories = [d.strip() for d in args.directory.split("\n") if d.strip()]
    
    checker = TerraformVersionChecker(
        github_token=args.github_token,
        patches_behind=args.patches_behind
    )
    
    # Get latest version
    print(f"🔍 Fetching Terraform version ({args.patches_behind} patch(es) behind latest)...")
    latest = checker.get_latest_terraform_version(args.patches_behind)
    print(f"✅ Target Terraform version: {latest}\n")
    
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
