FROM python:3.8-alpine
RUN apk update && apk add --no-cache build-base
ADD main.py /
ADD requirements.txt /
RUN pip install -r requirements.txt
CMD ["python", "./main.py"]