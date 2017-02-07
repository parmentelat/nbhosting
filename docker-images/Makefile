IMAGES = flotbioinfo flotpython datasciencehandbook 

all: $(IMAGES)

define image_target
$1:
	docker build -f $1.Dockerfile -t $1 .
endef

$(foreach image, $(IMAGES), $(eval $(call image_target, $(image))))
