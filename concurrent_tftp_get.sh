#!/bin/bash

# Configuration
TFTP_SERVER="127.0.0.1"
TFTP_PORT="69"
FILENAME="medium_file"  # Change this to your desired file
NUM_REQUESTS=10

echo "Starting $NUM_REQUESTS concurrent TFTP downloads..."

# Run 10 concurrent TFTP requests in the background
for i in {1..10}; do
    tftp "$TFTP_SERVER" "$TFTP_PORT" <<EOF > "output_${i}.txt" 2>&1 &
get $FILENAME
quit
EOF
done

# Wait for all background processes to complete
wait

echo "All downloads completed!"

# Check results
echo "Checking downloaded files..."
for i in {1..10}; do
    if [[ -f "output_${i}.txt" ]]; then
        size=$(wc -c < "output_${i}.txt" 2>/dev/null || echo "0")
        echo "output_${i}.txt: ${size} bytes"
    else
        echo "output_${i}.txt: MISSING"
    fi
done
