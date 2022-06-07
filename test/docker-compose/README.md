# test/docker-compose

## Setup the host

```
cd test/docker-compose
offtrops
export TROPS_DIR=$PWD/shared/trops
trops env create host
ontrops host
trops env update --git-remote=<remote_repo>
make all

# Create a first issue on GitLab/Github and then
ttags \#1
```

## Setup example1 - Normal user accout with sudo

```
docker-compose exec -u user1 -w /home/user1 -e TROPS_TAGS=$TROPS_TAGS example1 bash -i
trops env create --sudo=True --git-remote=<remote_repo> example1
ontrops example1
```

## Setup example2 and example3 - root access

```
# Example2
docker-compose exec -e TROPS_TAGS=$TROPS_TAGS example2 bash -i
trops env create --git-remote=<remote_repo> example2
ontrops example3

# Example2
docker-compose exec -e TROPS_TAGS=$TROPS_TAGS example3 bash -i
trops env create --git-remote=<remote_repo> example3
ontrops example3
```

## Rebuild containers

```
make rebuild_containers
```

## Clean up

```
# Clean up everything
offtrops
make clean

# Clean up trops directory
offtrops
make clean_trops_dir

# Clean up .ssh directories
make clean_keys

# Clean up containers
make clean_containers
```
