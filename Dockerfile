FROM python:latest

COPY . .

RUN pip install -r requirements.txt
#RUN apt-get install -y cron
#RUN crontab crontab
#
#CMD ["crond", "-f"]
CMD ["python",  "/refresh_playlists.py"]