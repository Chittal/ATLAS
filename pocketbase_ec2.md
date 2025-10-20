ssh -i "pocketbase-key.pem" ubuntu@ec2-18-204-231-148.compute-1.amazonaws.com


# Connect to your instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install PocketBase
wget https://github.com/pocketbase/pocketbase/releases/download/v0.21.3/pocketbase_0.21.3_linux_amd64.zip
unzip pocketbase_0.21.3_linux_amd64.zip
chmod +x pocketbase

# Run PocketBase
./pocketbase serve --http=0.0.0.0:8090