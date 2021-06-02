#!/bin/bash
commit_id=${BUILD_ID}-$(git rev-parse --short HEAD)
echo $commit_id> commit_id.txt
docker build -t crawlercontainerregistry.azurecr.io/$image_name:$commit_id .
az acr login -n CrawlerContainerRegistry -u $acr-registry_user -p $acr-registry_pass
#docker login -u $acr-registry_user -p $acr-registry_pass crawlercontainerregistry.azurecr.io
docker push crawlercontainerregistry.azurecr.io/$image_name:$commit_id





#commit_id=${BUILD_ID}-$(git rev-parse --short HEAD)
#echo $commit_id> commit_id.txt
#docker build -t anuvaadio/$image_name:$commit_id .
#docker login -u $dockerhub_user -p $dockerhub_pass
#docker push anuvaadio/$image_name:$commit_id
