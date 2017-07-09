# run make BUILDOPTS="--no-cache" to force rebuild

IMAGES = flotpython flotbioinfo datasciencehandbook 

all: $(IMAGES)

define image_target
$1:
	docker build $(BUILDOPTS) -f $1.Dockerfile -t $1 .
endef

$(foreach image, $(IMAGES), $(eval $(call image_target, $(image))))
