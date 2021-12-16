 
DJANGO   := phillipjensen/golemgrid-container-manager
IMG_DJANGO    := ${DJANGO}:${GITHUB_SHA}

CELERY   := phillipjensen/golemgrid-container-manager-celery
IMG_CELERY    := ${CELERY}:${GITHUB_SHA}

CELERY_BEAT   := phillipjensen/golemgrid-container-manager-celery-beat
IMG_CELERY_BEAT    := ${CELERY_BEAT}:${GITHUB_SHA}
 
 
buildarm:
	@docker buildx create --use	
	@docker buildx build --platform=linux/arm64,linux/amd64 --push -t ${IMG_DJANGO} -t ${DJANGO}:latest -f ./dockerfiles/Django .
	@docker buildx build --platform=linux/arm64,linux/amd64 --push -t ${IMG_CELERY} -t ${CELERY}:latest -f ./dockerfiles/Celery .
	@docker buildx build --platform=linux/arm64,linux/amd64 --push -t ${IMG_CELERY_BEAT} -t ${CELERY_BEAT}:latest -f ./dockerfiles/Beat .

login:
	@docker login -u ${DOCKER_USER} -p ${DOCKER_PASS}


build:
	@docker build -t ${IMG_DJANGO} -t ${DJANGO}:latest -f ./dockerfiles/Django .
	@docker build -t ${IMG_CELERY} -t ${CELERY}:latest -f ./dockerfiles/Celery .
	@docker build -t ${IMG_CELERY_BEAT} -t ${CELERY_BEAT}:latest -f ./dockerfiles/Beat .
	@docker tag ${IMG_DJANGO} ${IMG_DJANGO} && docker tag ${DJANGO}:latest ${DJANGO}:latest
	@docker tag ${IMG_CELERY} ${IMG_CELERY} && docker tag ${CELERY}:latest ${CELERY}:latest
	@docker tag ${IMG_CELERY_BEAT} ${IMG_CELERY_BEAT} && docker tag ${CELERY_BEAT}:latest ${CELERY_BEAT}:latest

push:
	@docker push ${IMG_DJANGO} && docker push ${DJANGO}
	@docker push ${IMG_CELERY} && docker push ${CELERY}
	@docker push ${IMG_CELERY_BEAT} && docker push ${CELERY_BEAT}