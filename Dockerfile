# pl-freesurfer: FreeSurfer's own image, plus a system Python and this package.
#
# The base carries FreeSurfer under FREESURFER_HOME with its programs on PATH and
# its own interpreter, fspython, for its own scripts. Rocky Linux 8's python3 is
# 3.6, so Python 3.12 is installed from AppStream and the package goes into it;
# the console script lands in /usr/local/bin, which the base already has on PATH.
# FreeSurfer's own python3 is left alone, since its scripts do not depend on this one.
#
# The base also carries a bash script named freesurfer in $FREESURFER_HOME/bin, which
# prints a welcome banner and is first on PATH; it would shadow the plugin's console
# script, and chris_plugin_info would record its path as the plugin's. /usr/local/bin
# is put ahead of it so that the command freesurfer is the plugin's.
#
# Build and check locally:
#
#   docker build -t localhost/fnndsc/pl-freesurfer:1.0.1 .
#   docker run --rm localhost/fnndsc/pl-freesurfer:1.0.1 freesurfer --version
#
# The image is some 26 GB unpacked; CI frees the runner's disk before building it.

FROM docker.io/freesurfer/freesurfer:8.2.0

LABEL org.opencontainers.image.authors="FNNDSC <dev@babyMRI.org>" \
      org.opencontainers.image.title="pl-freesurfer" \
      org.opencontainers.image.description="FreeSurfer 8.2 recon-all over every subject directory of an input tree: a ChRIS DS plugin on pl-shexec" \
      org.opencontainers.image.source="https://github.com/FNNDSC/pl-freesurfer" \
      org.opencontainers.image.version="1.0.1" \
      freesurfer.version="8.2.0"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PATH=/usr/local/bin:${PATH}

RUN dnf install -y python3.12 python3.12-pip \
    && dnf clean all \
    && rm -rf /var/cache/dnf

# The licence is for research use, as pl-fshack carried it; a site mounts its own over this path.
COPY license.txt ${FREESURFER_HOME}/license.txt
ENV FS_LICENSE=${FREESURFER_HOME}/license.txt

WORKDIR /usr/local/src/pl-freesurfer
COPY . .
RUN python3.12 -m pip install --no-cache-dir .

CMD ["freesurfer", "--man"]
