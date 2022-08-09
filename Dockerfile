FROM python:3.10.4-slim-buster

ENV SRCDIR /src
RUN mkdir -p $SRCDIR/app && chown -R root:root $SRCDIR

WORKDIR $SRCDIR

COPY requirements.txt $SRCDIR
RUN pip3 install -r requirements.txt

COPY . $SRCDIR
EXPOSE 5000
WORKDIR $SRCDIR/app

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "wsgi:app"]
