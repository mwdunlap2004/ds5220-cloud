"""
Generates a CSV file with a random 12-character filename,
fills it with a random number of lines of random words,
uploads it to an S3 bucket, and deletes the local file.

Usage:
    python generate-and-upload.py <bucket-name> <count>
"""

import sys
import os
import random
import string
import boto3

WORDS = [
    "apple", "river", "mountain", "cloud", "forest", "bridge", "garden",
    "silver", "thunder", "meadow", "crystal", "voyage", "harbor", "sunset",
    "lantern", "compass", "falcon", "marble", "shadow", "breeze", "canyon",
    "ember", "glacier", "horizon", "island", "jungle", "kettle", "lighthouse",
    "nectar", "orchid", "pebble", "quartz", "ribbon", "sapphire", "tornado",
    "umbrella", "velvet", "willow", "zenith", "anchor", "blossom", "comet",
    "dolphin", "eclipse", "fountain", "granite", "hummingbird", "ivory",
]


def generate_filename():
    """Return a random 12-character alphanumeric filename with .csv extension."""
    chars = string.ascii_lowercase + string.digits
    name = "".join(random.choices(chars, k=12))
    return f"{name}.csv"


def generate_csv(filename):
    """Write a CSV with a random number of lines (400-1700) of random words."""
    num_lines = random.randint(400, 1700)
    with open(filename, "w") as f:
        f.write("col1,col2,col3,col4,col5\n")
        for _ in range(num_lines):
            line = ",".join(random.choices(WORDS, k=5))
            f.write(line + "\n")
    print(f"Created {filename} with {num_lines} lines")
    return filename


def upload_to_s3(filename, bucket):
    """Upload the file to the given S3 bucket and delete the local copy."""
    s3 = boto3.client("s3")
    s3.upload_file(filename, bucket, filename)
    print(f"Uploaded {filename} to s3://{bucket}/{filename}")
    os.remove(filename)
    print(f"Deleted local file {filename}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate-and-upload.py <bucket-name> <count>")
        sys.exit(1)

    bucket_name = sys.argv[1]
    count = int(sys.argv[2])
    for i in range(count):
        fname = generate_filename()
        generate_csv(fname)
        upload_to_s3(fname, bucket_name)
    print(f"Done. Uploaded {count} files to s3://{bucket_name}/")
