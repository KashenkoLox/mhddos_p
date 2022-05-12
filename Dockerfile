FROM --platform=$BUILDPLATFORM python:3.10-alpine as builder
RUN apk update && apk add --update git gcc libc-dev libffi-dev
WORKDIR mhddos_p
COPY ./requirements.txt .
RUN pip3 install --target=/mhddos_p/dependencies -r requirements.txt
COPY . .

FROM python:3.10-alpine
WORKDIR mhddos_p
COPY --from=builder	/mhddos_p .
ENV PYTHONPATH="${PYTHONPATH}:/mhddos_p/dependencies" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["python3", "./runner.py"]
