FROM python:3.11-slim

WORKDIR /code

# Install dependencies early to use Docker layer caching
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Create a non-root user to comply with Hugging Face Space security requirements
RUN useradd -m -u 1000 user
USER user

# Copy the rest of the application files securely
COPY --chown=user . /code

# Define standard port for HuggingFace
ENV PORT=7860
EXPOSE 7860

# Run the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
