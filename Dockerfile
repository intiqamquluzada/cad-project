FROM python:3.10

# Ensure that Python outputs everything that's printed inside
ENV PYTHONUNBUFFERED 1
ENV APP_ROOT /code
ENV DEBUG False

# Copy in your requirements file
COPY requirements.txt /requirements.txt

# Install dependencies
RUN pip3 install virtualenvwrapper && \
    python3 -m venv /venv && \
    /venv/bin/pip3 install -U pip && \
    /venv/bin/pip3 install --no-cache-dir -r /requirements.txt

# Copy your application code to the container
RUN mkdir ${APP_ROOT}
WORKDIR ${APP_ROOT}
COPY . ${APP_ROOT}

# uWSGI will listen on this port
EXPOSE 8000

# Start uWSGI
CMD [ "/venv/bin/uwsgi", "--ini", "/code/uwsgi.ini"]