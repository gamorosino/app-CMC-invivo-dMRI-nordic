FROM swarrington1/cmc-invivo:v0.1.0

# The base image runs as a non-root user; switch to root to write into /opt/venv.
USER root

# Add Python NORDIC dependencies on top of the CMC pipeline image.
# JAX CPU-only build; GPU variant (jax[cuda12]) can be used instead on GPU nodes.
RUN pip3 install --no-cache-dir \
    "jax==0.11.2" \
    "jaxlib==0.11.2" \
    "nibabel==5.4.2" \
    "scipy==1.18.1" \
    "numpy==2.5.3" \
    "matplotlib==3.11.2"

COPY nordic/ /opt/nordic/
