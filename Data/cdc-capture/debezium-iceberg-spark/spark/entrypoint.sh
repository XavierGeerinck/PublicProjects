#/bin/bash
cd workspace

echo "Starting Jupyter Lab"
jupyter-lab \
  --ip='*' \
  --NotebookApp.token='' \
  --NotebookApp.password='' \
  --port=8888 \
  --no-browser