# an attempt at clearing stuff up more quickly
# this allows to kill and remove all test dockers
# with e.g. 10 parallel jobs with
# make -j 10 clear-tests

# the thing is the docker daemon works as a bootleneck
# so it doesn't work as well as it should, but it's a bit better
# than purely sequential though

# all the docker here are test dockers
RUNNING-DOCKERS = $(shell docker ps --format '{{.Names}}'    | grep -- -x-student-)
IDLE-DOCKERS    = $(shell docker ps --format '{{.Names}}' -a | grep -- -x-student-)

clear-tests: kill-dockers remove-dockers

kill-targets = $(foreach docker,$(RUNNING-DOCKERS),$(docker).kill)
kill-dockers: $(kill-targets)

remove-targets = $(foreach docker,$(IDLE-DOCKERS),$(docker).remove)
remove-dockers: $(remove-targets)

define all-targets
$(1).kill:
	docker kill $(1)
$(1).remove:
	docker rm $(1)
endef

$(foreach docker, $(IDLE-DOCKERS), $(eval $(call all-targets,$(docker))))

