FROM python:3.12-slim
RUN python3 -m pip install requests
COPY joke.py /joke.py
ENTRYPOINT ["python3", "joke.py"]

