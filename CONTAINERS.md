# Deploying each container separately

## MVP (End-to-End Case)

### Network

    docker network create -d bridge perseus-net

### Shared db

    cd shareddb
    docker build -t shareddb .
    docker run --name shareddb -d -p 5432:5432 --network=perseus-net shareddb

### Files manager

    cd files-manager
    docker build -t files-manager .
    docker run --name files-manager -d -p 10500:10500 -e SPRING_PROFILES_ACTIVE='docker' --network=perseus-net files-manager

### Backend

    cd perseus-api
    docker build -t backend .
    docker run --name backend -d -p 5000:5000 -e PERSEUS_ENV='Docker' --network=perseus-net backend

### User

    cd user
    docker build -t user .
    docker run --name user -d -p 5001:5001 -e USER_ENV='Docker' --network=perseus-net user

### Frontend
    
    cd UI
    docker build -t frontend --build-arg env='prod' .
    docker run --name frontend -d -p 4200:4200 --network=perseus-net frontend

### Web
    
    cd nginx
    docker build -t web .
    docker run --name web -d -p 80:80 --network=perseus-net web

### White Rabbit

    cd ../WhiteRabbit
    docker build -t white-rabbit .
    docker run --name white-rabbit -d -p 8000:8000 -e SPRING_PROFILES_ACTIVE='docker' --network=perseus-net white-rabbit

### Vocabulary db

    cd vocabulary-db
    docker build -t vocabularydb .
    docker run --name vocabularydb -d -p 5431:5432 --network=perseus-net vocabularydb

### CDM Builder
    
    cd ../ETL-CDMBuilder
    docker build -t cdm-builder -f "source/org.ohdsi.cdm.presentation.builderwebapi/Dockerfile" .
    docker run --name cdm-builder -d -p 9000:9000 --network=perseus-net cdm-builder

## Additional features

## R Server

    cd ../DataQualityDashboard/R
    docker build -t r-serve --build-arg prop='docker' .
    docker run --name r-serve -d -p 6311:6311 --network=perseus-net r-serve

## Data Quality Dashboard
    
    cd ../DataQualityDashboard
    docker build -t data-quality-dashboard .
    docker run --name data-quality-dashboard -d -p 8001:8001 -e SPRING_PROFILES_ACTIVE='docker' --network=perseus-net data-quality-dashboard

### Solr

    cd solr
    docker build -t solr .
    docker run --name solr -d -p 8983:8983 --network=perseus-net solr

### Athena

    cd athena-api
    docker build -t athena .
    docker run --name athena -d -p 5002:5002 -e ATHENA_ENV='Docker' --network=perseus-net athena

    
    