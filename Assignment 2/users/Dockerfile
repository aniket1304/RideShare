FROM python
ADD . /todo
WORKDIR /todo
RUN pip install -r requirements.txt
EXPOSE 8080
ENV TEAM_NAME=CC_130_185_252_279
CMD ["python","user.py"]
