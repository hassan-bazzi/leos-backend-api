NOW=$(date +"%Y-%m-%d-%H:%M")
docker build -t leos-$NOW $1
