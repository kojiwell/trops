.PHONY: build_example1 build_example2 build_example3 \
	login_example1 login_example2 login_example3 \
	clean_containers clean_keys clean_trops_dir \
	start_containers rebuild_containers print_ssh_pubkey \
	all clean

DATE := $(shell date "+%F %R")
TROPS_TAGS := ${TROPS_TAGS}

example1/root/.ssh \
example2/root/.ssh \
example3/root/.ssh \
example1/home/user1/.ssh:
	test -d $@ || mkdir -p $@

example1/root/.ssh/id_ed25519:
	ssh-keygen -t ed25519 -N "" -C "test-key $(DATE)" -f $@

example2/root/.ssh/id_ed25519 \
example3/root/.ssh/id_ed25519 \
example1/home/user1/.ssh/id_ed25519:
	cp example1/root/.ssh/id_ed25519 $@
	cp example1/root/.ssh/id_ed25519.pub $@.pub

example1/root/.ssh/known_hosts:
	ssh-keyscan -t ssh-ed25519,ecdsa-sha2-nistp256 gitlab.com > $@
	ssh-keyscan -t ssh-ed25519,ecdsa-sha2-nistp256 github.com >> $@

example2/root/.ssh/known_hosts \
example3/root/.ssh/known_hosts \
example1/home/user1/.ssh/known_hosts:
	cp example1/root/.ssh/known_hosts $@

ssh_dirs: example1/root/.ssh example2/root/.ssh example3/root/.ssh example1/home/user1/.ssh
ssh_keys: ssh_dirs example1/root/.ssh/id_ed25519 example2/root/.ssh/id_ed25519 example3/root/.ssh/id_ed25519 example1/home/user1/.ssh/id_ed25519
ssh_known_hosts: ssh_dirs example1/root/.ssh/known_hosts example2/root/.ssh/known_hosts example3/root/.ssh/known_hosts example1/home/user1/.ssh/known_hosts

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
	docker-compose exec -e TROPS_TAGS=$(TROPS_TAGS) example1 bash -i

login_example2:
	docker-compose exec -e TROPS_TAGS=$(TROPS_TAGS) example2 bash -i

login_example3:
	docker-compose exec -e TROPS_TAGS=$(TROPS_TAGS) example3 bash -i

clean_containers:
	docker-compose down

clean_keys:
	rm -rf example1/root/.ssh 	example2/root/.ssh 	example3/root/.ssh example1/home/user1/.ssh

clean_trops_dir:
	docker-compose exec example1 chown -R user1:user1 /opt/shared/trops
	rm -rf shared/trops/*

start_containers:
	docker-compose up -d

rebuild_containers: clean_containers build_containers start_containers

print_ssh_pubkey:
	cat example1/root/.ssh/id_ed25519.pub

all: ssh_keys ssh_known_hosts build_containers start_containers print_ssh_pubkey

clean: clean_keys clean_trops_dir clean_containers 