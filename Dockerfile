FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV NVIDIA_VISIBLE_DEVICES all
EXPOSE 8000

ENTRYPOINT [ "python", "/usr/src/app/main.py" ]