# test/docker-compose

## Setup the environment

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

## Example1

```
# login and setup as root
docker-compose exec -e TROPS_TAGS=$TROPS_TAGS example1 bash -i
trops env create example1

# login and setup as user1
docker-compose exec -u user1 -w /home/user1 -e TROPS_TAGS=$TROPS_TAGS example1 bash -i
trops env create user1
```

## Example2 and Example3

```
# Example2
docker-compose exec -e TROPS_TAGS=$TROPS_TAGS example2 bash -i
trops env create example2
ontrops example3

# Example2
docker-compose exec -e TROPS_TAGS=$TROPS_TAGS example3 bash -i
trops env create example3
ontrops example3
```

## Rebuild containers

```
make rebuild_containers
```

## Clean up

```
# Clean up everything
make clean

# Clean up trops directory
offtrops
make clean_trops_dir

# Clean up .ssh directories
make clean_keys

# Clean up containers
make clean_containers
```
