# syntax=docker/dockerfile:1.2

# GOALS:
# 1. Download SCP:SL
# 2. Publicize the DLL
# 3. Build EXILED
# 4. Create container for dedicated server
# 5. Create container for plugin building

# Download SCP:SL
# As the Mono image also uses this image as a base, also use it here to help with layer caching
FROM debian:buster-slim as steam

RUN useradd -ms /bin/bash steam

# This is a sentinel file used for cache invalidation
# Change this file when SL updates and Docker will reinstall SL
COPY scp-sl-version .

# 3008: intentionally allowing updates from apt
# 4006: because echo can't fail
# hadolint ignore=DL3008,DL4006
RUN sed -i "s/main/main non-free/g" /etc/apt/sources.list \ 
 && dpkg --add-architecture i386 \
 && apt-get update \
 && echo steamcmd steam/question select "I AGREE" | debconf-set-selections \
 && echo steamcmd steam/license note '' | debconf-set-selections \
 && apt-get install -y --no-install-recommends ca-certificates lib32gcc1 steamcmd

USER steam
WORKDIR /home/steam
# Install the SL dedicated server in /home/steam/scpslds
RUN /usr/games/steamcmd +login anonymous +force_install_dir /home/steam/scpslds +app_update 996560 -beta 10.2.2 +quit

## C# Setup
# These containers are a generic base for building and running C# code
# We need the fat version for msbuild and nuget
FROM mono:6.12 as cs-build
RUN useradd -u 2965 -ms /bin/bash build
WORKDIR /home/build
USER build

# APublicizer requires C# 9.0/.NET 5.0, so create a special .NET 5.0 container
# Exiled.Patcher also needs .NET Core
FROM mcr.microsoft.com/dotnet/sdk:5.0-buster-slim as cs5-build
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
RUN useradd -u 2965 -ms /bin/bash build
WORKDIR /home/build
USER build

# Small Runtime container for running C# code with Mono
FROM mono:6.12-slim as cs-run
RUN useradd -ms /bin/bash run
WORKDIR /home/run
USER run

## End of C# containers

# We need to publicize the DLL for EXILED's build
FROM cs5-build as apublicizer

COPY --chown=build:build APublicizer APublicizer
WORKDIR /home/build/APublicizer
RUN dotnet build /property:Configuration=Release
COPY --from=steam /home/steam/scpslds/SCPSL_Data/Managed/*.dll ./
RUN ./bin/Release/APublicizer Assembly-CSharp.dll

# Build EXILED
FROM cs-build as exiled-build

COPY --chown=build:build EXILED EXILED
WORKDIR /home/build/EXILED
ENV EXILED_REFERENCES=/home/build/Managed
RUN --mount=type=cache,id=nuget,target=/home/build/.local/share/NuGet/,uid=2965 \
  for project in API Bootstrap CreditTags Events Example Loader Permissions Updater; \
  do \
    msbuild -t:restore Exiled.$project; \
  done


# Assemble the references
COPY --from=steam /home/steam/scpslds/SCPSL_Data/Managed/*.dll /home/build/Managed/
COPY --from=apublicizer /home/build/APublicizer/Assembly-CSharp-Publicized.dll /home/build/Managed/
# Build the actual thing
RUN msbuild /property:Configuration=Release
# Build an install dir
COPY ./scripts/assemble-exiled.sh .
RUN ./assemble-exiled.sh

# Build EXILED's patcher to create the patched Assembly-CSharp.dll
# By default, this uses .NET Core 3.1, but we override this to .NET 5.0.
FROM cs5-build as exiled-patcher-build

COPY --chown=build:build EXILED EXILED
WORKDIR /home/build/EXILED/Exiled.Patcher
RUN --mount=type=cache,id=nuget,target=/home/build/.local/share/NuGet/,uid=2965 dotnet restore -p:TargetFramework=net5.0
RUN dotnet build --configuration Release --runtime linux-x64 -p:TargetFramework=net5.0
# Run the patcher. It injects Exiled.Bootstrap.dll into Assembly-CSharp.dll, then writes it as Assembly-CSharp-Exiled.dll
COPY --from=steam /home/steam/scpslds/SCPSL_Data/Managed/Assembly-CSharp.dll .
COPY --from=exiled-build /home/build/EXILED/bin/Release/Exiled.Bootstrap.dll .
RUN ./bin/Release/linux-x64/Exiled.Patcher-Linux Assembly-CSharp.dll

FROM cs-build as plugin-build

# Assemble the references
ENV EXILED_REFERENCES=/home/build/Managed
COPY --from=steam /home/steam/scpslds/SCPSL_Data/Managed/*.dll /home/build/Managed/
COPY --from=apublicizer /home/build/APublicizer/Assembly-CSharp-Publicized.dll /home/build/Managed/
COPY --from=exiled-build /home/build/EXILED/bin/Release/*.dll /home/build/Managed/
RUN mkdir plugin obj bin

WORKDIR /home/build/plugin
ENTRYPOINT ["/usr/bin/msbuild"]

FROM cs-run as server-run

USER root
RUN apt-get update \
 && apt-get install -y libicu63=63.1-6+deb10u1 tini=0.18.0-1 --no-install-recommends \
 && apt-get clean \
 && rm -r /var/lib/apt/lists/* \
 && mkdir -p "/home/run/.config/SCP Secret Laboratory/" \
 && chown run:run "/home/run/.config/SCP Secret Laboratory/"

USER run

COPY ./scripts/run-exiled.sh /home/run/run-exiled.sh
COPY --from=steam /home/steam/scpslds/ /home/run/scpslds/
COPY --from=exiled-patcher-build /home/build/EXILED/Exiled.Patcher/Assembly-CSharp-Exiled.dll /home/run/scpslds/SCPSL_Data/Managed/Assembly-CSharp.dll
COPY --from=exiled-build /home/build/artifacts/EXILED /home/run/EXILED

EXPOSE 7777/udp
WORKDIR /home/run/scpslds
CMD ["/usr/bin/tini", "/home/run/run-exiled.sh", "/home/run/scpslds/LocalAdmin", "7777"]
