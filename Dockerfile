# ใช้ Python base image
FROM python:3.11-slim

# ติดตั้ง dependency พื้นฐาน + git
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        git build-essential wget curl zip unzip \
        apt-transport-https ca-certificates gnupg lsb-release && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /scripts

# ติดตั้ง Python dependencies ก่อน (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ ติดตั้ง Sigma (เวอร์ชันล่าสุดจาก GitHub)
RUN git clone https://github.com/SigmaHQ/sigma.git /opt/sigma && \
    cd /opt/sigma/tools && \
    pip install .

# เพิ่ม PATH เผื่อ local install
ENV PATH="/root/.local/bin:${PATH}"

# คัดลอก script และ config ของคุณเข้า image
COPY scripts/ .
COPY sigma-rule-configs/ .

# ✅ ตรวจสอบว่า sigmac ใช้งานได้ (lucene/kibana targets)
RUN sigmac --list-targets && sigmac -h

# Default command (optional)
CMD ["bash"]
