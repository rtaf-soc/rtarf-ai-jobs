# ใช้ Python base image (เลือก 3.11 หรือ 3.10 ตามต้องการ)
FROM python:3.11-slim

RUN apt-get update -qq && \
    apt-get install -y git build-essential wget curl zip unzip apt-transport-https ca-certificates gnupg lsb-release && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /scripts

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PATH="/root/.local/bin:${PATH}"

COPY scripts/ .
COPY sigma-rule-configs/ .

# Testing installation
RUN sigmac -h && ls -lrt /scripts/
