FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /src

COPY pom.xml .
COPY src ./src
RUN mvn -q -DskipTests -Dmaven.wagon.http.retryHandler.count=5 package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /src/target/geography-service-0.1.0.jar /app/geography-service.jar
EXPOSE 8000
ENTRYPOINT ["java", "-jar", "/app/geography-service.jar", "--server.port=8000"]
