FROM python:3.12-slim

# Install the Lambda Runtime Interface Client
RUN pip install awslambdaric

COPY app.py /app/
WORKDIR /app

ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["app.handler"]
