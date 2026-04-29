FROM eclipse-temurin:17-jre
WORKDIR /app
COPY application.yml application.yml
ADD https://github.com/lavalink-devs/Lavalink/releases/download/4.0.8/Lavalink.jar Lavalink.jar
CMD ["java", "-jar", "Lavalink.jar"]
