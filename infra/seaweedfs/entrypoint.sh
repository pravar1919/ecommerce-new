#!/bin/sh
# Dev-only S3 server (SeaweedFS: master + volume + filer + S3 gateway in one process).
# 1. writes the S3 identity config from env
# 2. starts SeaweedFS
# 3. ensures the media bucket exists, then marks the container ready (see healthcheck)
# Public-read on the public/ prefix is applied by the s3-init service (bucket-policy.json).
set -eu
rm -f /tmp/ready
cat > /tmp/s3.json <<JSON
{
  "identities": [
    { "name": "app",
      "credentials": [{ "accessKey": "${AWS_ACCESS_KEY_ID}", "secretKey": "${AWS_SECRET_ACCESS_KEY}" }],
      "actions": ["Admin", "Read", "Write", "List", "Tagging"] }
  ]
}
JSON

weed server -dir=/data -ip=127.0.0.1 -ip.bind=0.0.0.0 \
  -master.volumeSizeLimitMB=256 -volume.max=20 \
  -s3 -s3.port=9000 -s3.config=/tmp/s3.json &
WEED_PID=$!
trap 'kill -TERM $WEED_PID; wait $WEED_PID' TERM INT

until wget -q -O /dev/null http://127.0.0.1:9000/healthz; do sleep 1; done
if echo "s3.bucket.list" | weed shell -master=127.0.0.1:9333 2>/dev/null | grep -qw "${AWS_STORAGE_BUCKET_NAME}"; then
  echo "bucket ${AWS_STORAGE_BUCKET_NAME} exists"
else
  echo "s3.bucket.create -name ${AWS_STORAGE_BUCKET_NAME}" | weed shell -master=127.0.0.1:9333
  echo "bucket ${AWS_STORAGE_BUCKET_NAME} created"
fi
touch /tmp/ready
wait $WEED_PID
