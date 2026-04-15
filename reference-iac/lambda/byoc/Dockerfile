FROM python:3.12-slim

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

COPY app.py /app/
WORKDIR /app

ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["app.handler"]
