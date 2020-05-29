# an attempt at clearing stuff up more quickly
# this allows to kill and remove all test containers
# with e.g. 10 parallel jobs with
# make -j 10 clear-tests

ENGINE = podman

# all the container here are test containers
RUNNING-CONTAINERS = $(shell $(ENGINE) ps --format '{{.Names}}'    | grep -- -x-student-)
IDLE-CONTAINERS    = $(shell $(ENGINE) ps --format '{{.Names}}' -a | grep -- -x-student-)

clear-tests: kill-containers remove-containers

kill-targets = $(foreach container,$(RUNNING-CONTAINERS),$(container).kill)
kill-containers: $(kill-targets)

remove-targets = $(foreach container,$(IDLE-CONTAINERS),$(container).remove)
remove-containers: $(remove-targets)

define all-targets
$(1).kill:
	$(ENGINE) kill $(1)
$(1).remove:
	$(ENGINE) rm $(1)
endef

$(foreach container, $(IDLE-CONTAINERS), $(eval $(call all-targets,$(container))))

