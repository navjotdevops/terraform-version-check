FROM python:3.11-slim

LABEL maintainer="singh.navjot737@gmail.com"
LABEL org.opencontainers.image.source="https://github.com/navjotdevops/terraform-version-check"
LABEL org.opencontainers.image.description="GitHub Action to check Terraform versions and suggest upgrades"

# Install dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copy the action script
COPY terraform_version_checker.py /terraform_version_checker.py
RUN chmod +x /terraform_version_checker.py

# Set working directory
WORKDIR /github/workspace

# Set entrypoint
ENTRYPOINT ["python", "/terraform_version_checker.py"]
