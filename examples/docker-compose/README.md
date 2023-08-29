# Examples using Docker Compose

## Setup the host

```
cd examples/docker-compose
offtrops
export TROPS_DIR=$PWD/shared/trops
trops env create host
ontrops host
trops env update --git-remote=<remote_repo>
make all

# Create a first issue on GitLab/Github and then
ttags \#1
```

## Setup example1 - Normal user with sudo

```
make login_example1
trops env create --sudo=True --git-remote=<remote_repo> example1
ontrops example1
```

## Setup example2 and example3 - root user

```
# Example2
make login_example2
trops env create --git-remote=<remote_repo> example2
ontrops example3

# Example2
make login_example3
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
