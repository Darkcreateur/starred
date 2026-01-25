FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/yourusername/starred"
LABEL org.opencontainers.image.description="AI-powered GitHub Stars Organizer"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install all LLM providers
RUN pip install --no-cache-dir anthropic openai google-generativeai

# Copy source code
COPY src/ src/
COPY pyproject.toml .

# Install package
RUN pip install --no-cache-dir -e .

# Create directories
RUN mkdir -p /app/data /output

# Set environment
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["starred"]
CMD ["--help"]
