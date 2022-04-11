import os
import json
import sys
import shutil
import urllib2
import zipfile
import tarfile
import subprocess
import ssl
import argparse


THIS_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


def __parse_args(args):
    args = args[1:]
    parser = argparse.ArgumentParser(description='The root build script.')

    parser.add_argument('--sdk_download_url', type=str, default='')
    parser.add_argument('--sdk_zip_root_folder', type=str, default='')

    return parser.parse_args(args)


def __unzip_file(src_zip_file, dst_folder):
    if src_zip_file.endswith('.tar') or src_zip_file.endswith('.gz'):
        with tarfile.open(src_zip_file, 'r:gz') as f:
            f.extractall(dst_folder)
    elif src_zip_file.endswith('.zip'):
        if sys.platform == 'win32':
            with zipfile.ZipFile(src_zip_file, 'r') as f:
                f.extractall(dst_folder)
        else:
            subprocess.check_call(['unzip', '-o', '-q', src_zip_file, '-d', dst_folder])


def main(argv):
    args = __parse_args(argv)
    print("arguments: {}".format(args))
    print(sys.version)

    if len(args.sdk_download_url) == 0:
        raise Exception("SDK URL must not be EMPTY!")

    dst_libs_path = os.path.join(THIS_SCRIPT_PATH, 'libs')
    dst_jni_path = os.path.join(THIS_SCRIPT_PATH, 'src', 'main', 'jniLibs')

    if os.path.exists(dst_libs_path):
        shutil.rmtree(dst_libs_path, ignore_errors=True)
    os.mkdir(dst_libs_path)

    if os.path.exists(dst_jni_path):
        shutil.rmtree(dst_jni_path, ignore_errors=True)
    os.mkdir(dst_jni_path)

    oss_url = args.sdk_download_url
    artifact_name = oss_url.split('/')[-1]
    artifact_name = artifact_name.split('?')[0] # remove url version

    request = urllib2.Request(oss_url)
    print('\n --> Request: "{}"'.format(oss_url))
    context = ssl._create_unverified_context()
    u = urllib2.urlopen(request, context=context)
    print(' <-- Response: "{}"'.format(u.code))

    artifact_path = os.path.join(THIS_SCRIPT_PATH, artifact_name)
    with open(artifact_path, 'wb') as fw:
        fw.write(u.read())

    tmp_dst_unzip_folder = os.path.join(THIS_SCRIPT_PATH, '__tmp__')
    __unzip_file(artifact_path, tmp_dst_unzip_folder)

    if len(args.sdk_zip_root_folder) == 0:
        for folder in os.listdir(tmp_dst_unzip_folder):
            product_folder = os.path.join(tmp_dst_unzip_folder, folder)
            if os.path.isdir(product_folder):
                for f in os.listdir(product_folder):
                    if os.path.isdir(os.path.join(product_folder, f)):
                        shutil.copytree(os.path.join(product_folder, f), os.path.join(dst_jni_path, f))
                    else:
                        shutil.copy(os.path.join(product_folder, f), os.path.join(dst_libs_path))

                break
    else:
        product_folder = os.path.join(tmp_dst_unzip_folder, args.sdk_zip_root_folder)
        for f in os.listdir(product_folder):
            if os.path.isdir(os.path.join(product_folder, f)):
                shutil.copytree(os.path.join(product_folder, f), os.path.join(dst_jni_path, f))
            else:
                shutil.copy(os.path.join(product_folder, f), os.path.join(dst_libs_path))

    print("Download SDK success")

    shutil.rmtree(tmp_dst_unzip_folder, ignore_errors=True)
    os.remove(artifact_path)

    # Remove BuildConfig.class
    for jar in os.listdir(dst_libs_path):
        if '.jar' in jar:
            os.chdir(dst_libs_path)
            subprocess.check_call(['jar', 'xf', os.path.join(dst_libs_path, jar)])

            for (root, dirs, files) in os.walk(dst_libs_path):
                for f in files:
                    if f == 'BuildConfig.class':
                        os.remove(os.path.join(root, f))
                        break

            os.remove(os.path.join(dst_libs_path, jar))
            subprocess.check_call(['jar', 'cf', os.path.join(dst_libs_path, jar), '.'])


if __name__ == '__main__':
    sys.exit(main(sys.argv))
