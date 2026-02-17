# Start from verified VEHU image
FROM worldvista/vehu:202504

USER root

# Enable PowerTools and install numerical/dev libraries
# Use 'dnf' (the modern yum) to enable the repository needed for blas/lapack
RUN dnf install -y 'dnf-command(config-manager)' && \
    dnf config-manager --set-enabled powertools && \
    dnf install -y \
    libffi-devel \
    python3-devel \
    atlas-devel \
    blas-devel \
    lapack-devel

# Install Python 3.11 (Rocky Linux 8 uses the 'python3.11' package directly)
RUN dnf install -y python3.11 python3.11-devel

# Set the symlink so 'python3' points to 3.11
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3

# Install Dependencies from requirements.txt
# Source the YDB environment so the yottadb-python wheel can find the C headers
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m ensurepip && \
    python3 -m pip install --upgrade pip && \
    /bin/bash -c "source /usr/local/etc/ydb_env_set && python3 -m pip install -r /tmp/requirements.txt"

USER root