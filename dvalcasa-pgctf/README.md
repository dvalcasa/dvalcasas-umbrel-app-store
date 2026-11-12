# pgCft Server

*Vapor back-end* with Supabase for paragliding game: **iPgCtf**

## Run with script

*          Start app : ./run.sh start                    (-u)
*    Stop Containers : ./run.sh stop         (-d)
*          Clean all : ./run.sh clean                    (-c)
*               Logs : ./run.sh logs                             (-l)
*            Initate : ./run.sh init                             (-i)

ex: stop clean and start app
```bash
./run.sh stop clean start
```
or
```bash
./run.sh -d -c -u
```

## .env file 

```yaml
LOG_LEVEL=debug

GHCR_USER=user
GHCR_TOKEN=token_ghcr

PGCTF_PORT=8080
API_GW_HTTP_PORT=8000
```
