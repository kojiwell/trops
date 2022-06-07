DATE := $(shell date +%F)

example1/root/.ssh \
example2/root/.ssh \
example3/root/.ssh \
example1/home/user1/.ssh:
	test -d $@ || mkdir -p $@

example1/root/.ssh/id_ed25519 \
example2/root/.ssh/id_ed25519 \
example3/root/.ssh/id_ed25519 \
example1/home/user1/.ssh/id_ed25519:
	ssh-keygen -t ed25519 -N "" -C "test-key $(DATE)" -f $@

ssh_dirs: example1/root/.ssh example2/root/.ssh example3/root/.ssh example1/home/user1/.ssh
ssh_keys: example1/root/.ssh/id_ed25519 example2/root/.ssh/id_ed25519 example3/root/.ssh/id_ed25519 example1/home/user1/.ssh/id_ed25519

build_example1: example1/root/.ssh example1/home/user1/.ssh \
				example1/root/.ssh/id_ed25519 example1/home/user1/.ssh/id_ed25519
	docker-compose build example1

build_example2:
	docker-compose build example2

build_example3:
	docker-compose build example3

build_containers:
	docker-compose build

login_example1:
	docker-compose exec example1 bash -i

login_example2:
	docker-compose exec example2 bash -i

login_example3:
	docker-compose exec example3 bash -i

clean_containers:
	docker-compose down

clean_keys:
	rm -rf example1/root/.ssh 	example2/root/.ssh 	example3/root/.ssh example1/home/user1/.ssh

start_containers:
	docker-compose up -d

all: clean_containers ssh_dirs ssh_keys build_containers start_containers

clean: clean_containers clean_keys