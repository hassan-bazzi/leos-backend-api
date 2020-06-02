#!/bin/bash

export AWS_ACCESS_KEY_ID=AKIAXXL43KVCME3CHMGP
export AWS_SECRET_ACCESS_KEY=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
export STRIPE_PUBLISHABLE_KEY=pk_test_DJB6cnzt7MGYzZjUYPmJjshv0065VauYwz
export STRIPE_SECRET_KEY=sk_test_jp7QLjfPzqquP5BIcaVJVGaH00ElhvnKtL
export TWILIO_ACCOUNT_SID=ACfaeafc3e4feedc41f14721c689b93d2e
export TWILIO_AUTH_TOKEN=be0acd4c74984df8c2f6639f8885b27f
export DEPLOY_ENV=uat

daemon() {
    chsum1=""

    while [[ true ]]
    do
        chsum2=`find /app -type f -exec md5sum {} \;`
        if [[ $chsum1 != $chsum2 ]] ; then
            kill -HUP $(ps aux|grep gunicorn |head -n 1 |awk {'print $2'})
            chsum1=$chsum2
        fi
        sleep 2
    done
}

daemon &

gunicorn --reload --chdir /app app -w 2 --threads 2  -b 0.0.0.0:8000

