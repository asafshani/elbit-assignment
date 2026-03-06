
FROM python:3.12-slim

# Create non-root user for security
RUN useradd -m -r appuser

# Set working directory
WORKDIR /app

# Copy application code
COPY app.py .

# Expose port
EXPOSE 8080

# Switch to non-root user
USER appuser

# Run the application
CMD ["python", "app.py"]