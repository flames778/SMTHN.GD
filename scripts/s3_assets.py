#!/usr/bin/env python3
"""Upload and download large assets to/from S3 using boto3.

Usage:
  python scripts/s3_assets.py upload --bucket my-bucket --key-prefix models assets/Miniforge3-MacOSX-x86_64.sh
  python scripts/s3_assets.py download --bucket my-bucket --key models/Miniforge3-MacOSX-x86_64.sh --out-dir assets

Requires AWS credentials in environment or configured via AWS CLI.
"""
import argparse
import os
import sys
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError
except Exception:
    print("boto3 is required for S3 helpers. Install with: pip install boto3")
    sys.exit(2)


def upload_file(s3, bucket, local_path, key):
    local_path = Path(local_path)
    if not local_path.exists():
        raise FileNotFoundError(local_path)
    try:
        print(f"Uploading {local_path} -> s3://{bucket}/{key}")
        s3.upload_file(str(local_path), bucket, key)
    except ClientError as e:
        raise


def download_file(s3, bucket, key, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        print(f"Downloading s3://{bucket}/{key} -> {out_path}")
        s3.download_file(bucket, key, str(out_path))
    except ClientError as e:
        raise


def upload_dir(s3, bucket, prefix, local_dir):
    local_dir = Path(local_dir)
    if not local_dir.is_dir():
        raise NotADirectoryError(local_dir)
    for p in sorted(local_dir.rglob('*')):
        if p.is_file():
            rel = p.relative_to(local_dir)
            key = (prefix + '/' if prefix else '') + str(rel).replace('\\\\', '/')
            upload_file(s3, bucket, p, key)


def main(argv=None):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd')

    up = sub.add_parser('upload')
    up.add_argument('--bucket', required=True)
    up.add_argument('--key-prefix', default='')
    up.add_argument('--recursive', action='store_true')
    up.add_argument('paths', nargs='+')

    down = sub.add_parser('download')
    down.add_argument('--bucket', required=True)
    down.add_argument('--key')
    down.add_argument('--key-prefix')
    down.add_argument('--out-dir', default='assets')
    down.add_argument('--recursive', action='store_true')

    args = p.parse_args(argv)
    session = boto3.session.Session()
    s3 = session.client('s3')

    if args.cmd == 'upload':
        for path in args.paths:
            if args.recursive and os.path.isdir(path):
                upload_dir(s3, args.bucket, args.key_prefix, path)
            else:
                key = (args.key_prefix + '/' if args.key_prefix else '') + os.path.basename(path)
                upload_file(s3, args.bucket, path, key)
    elif args.cmd == 'download':
        if args.key:
            out = Path(args.out_dir) / os.path.basename(args.key)
            download_file(s3, args.bucket, args.key, out)
        elif args.key_prefix and args.recursive:
            # list objects under prefix
            paginator = s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=args.bucket, Prefix=args.key_prefix):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    relative = key[len(args.key_prefix):].lstrip('/')
                    outpath = Path(args.out_dir) / relative
                    download_file(s3, args.bucket, key, outpath)
        else:
            raise ValueError('Provide --key or --key-prefix and --recursive')
    else:
        p.print_help()


if __name__ == '__main__':
    main()
