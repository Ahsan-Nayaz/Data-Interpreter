sudo blobfuse2 /home/azureuser/ssd/data --tmp-path=/mnt/resource/blobfusetmp  --config-file=/home/azureuser/ssd/config.yaml --allow-other
sudo blobfuse2 /home/azureuser/ssd/deployment/ --tmp-path=/mnt/resource/blobfusetmp  --config-file=/home/azureuser/ssd/deploy_config.yaml --allow-other
sudo python3.11 -m chainlit run app.py --port 80
