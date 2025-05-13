ARG BUILD_FROM
FROM $BUILD_FROM

COPY docker_entrypoint.sh /
RUN chmod a+x /docker_entrypoint.sh

CMD [ "/docker_entrypoint.sh" ]