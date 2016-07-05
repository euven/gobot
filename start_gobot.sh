#!/bin/sh

if [ -z "${GOBOT_PASSWORD}" ]; then
    GOBOT_PASSWORD="${JPASSWD}"; export GOBOT_PASSWORD
fi

exec python /gobot/gobot.py -j "${JID}" -r "${JROOM}" -n "${JNICK}" -g "${GODOMAIN}" -s "${GOSTAGES}"
