FROM python:3.8

RUN apt-get update && apt-get install -y vim
RUN pip install pandas

RUN pip install dash \
    dash-html-components \
    dash-daq \
    dash-core-components \
    dash-table \
    sqlalchemy \
    psycopg2

RUN pip install ipython
RUN pip install openpyxl
RUN pip install xlrd
RUN pip install names
RUN pip install jupyter
RUN pip install flask-keycloak dash-keycloak

RUN pip install gunicorn \
    scikit-learn \
    scipy \
    pillow

RUN pip install dash-bootstrap-components \
    matplotlib

RUN pip install \
    google-api-python-client \
    google-auth-httplib2 \
    google-auth-oauthlib

COPY /src /apps

WORKDIR /apps

EXPOSE 8050
RUN pip install git+https://github.com/plotly/dash-network.git
RUN pip install networkx
RUN pip install dash-auth==1.3.2

CMD ["python", "-m", "app"]
