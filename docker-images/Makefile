# run make BUILDOPTS="--no-cache" to force rebuild

KNOWN = $(patsubst %.Dockerfile,%,$(wildcard *.Dockerfile))
ALL = flotpython3

all: $(ALL)

define image_target
$1:
	docker build $(BUILDOPTS) -f $1.Dockerfile -t $1 .
endef

$(foreach image, $(KNOWN), $(eval $(call image_target, $(image))))
