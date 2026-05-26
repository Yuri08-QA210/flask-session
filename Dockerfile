FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN mkdir -p logs internal_assets && chmod 777 logs

COPY logs/app.log logs/app.log
COPY logs/security.log logs/security.log
COPY internal_assets/cerdentials.txt.bak internal_assets/cerdentials.txt.bak

RUN chmod 750 internal_assets && chmod 640 internal_assets/cerdentials.txt.bak

RUN useradd -m ctfuser && chown -R ctfuser:ctfuser /app
USER ctfuser

ENV SECRET_KEY=CTF_SECRET_DO_NOT_SHARE_2026
ENV ADMIN_OTP=OTP-7f3a9b2c

EXPOSE 5000
CMD ["python", "app.py"]
