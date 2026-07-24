import os
import sys
import shutil
import zipfile
import urllib.request
import subprocess

# Paths and URLs
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
WRAPPER_DIR = os.path.join(BASE_DIR, "android-wrapper")
ENV_DIR = os.path.join(WRAPPER_DIR, "build-env")

JDK_URL = "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/adoptium"
GRADLE_URL = "https://services.gradle.org/distributions/gradle-8.5-bin.zip"

JDK_ZIP = os.path.join(ENV_DIR, "jdk17.zip")
GRADLE_ZIP = os.path.join(ENV_DIR, "gradle85.zip")

JDK_EXTRACT_DIR = os.path.join(ENV_DIR, "jdk-17")
GRADLE_EXTRACT_DIR = os.path.join(ENV_DIR, "gradle-8.5")

ANDROID_SDK_DIR = r"C:\Users\admin\AppData\Local\Android\Sdk"

def print_progress(block_num, block_size, total_size):
    read_so_far = block_num * block_size
    if total_size > 0:
        percent = min(100, read_so_far * 100 // total_size)
        sys.stdout.write(f"\rDownloading... {percent}% ({read_so_far // (1024*1024)}MB / {total_size // (1024*1024)}MB)")
    else:
        sys.stdout.write(f"\rDownloading... {read_so_far // (1024*1024)}MB")
    sys.stdout.flush()

def download_file(url, dest_path, label):
    if os.path.exists(dest_path):
        print(f"[OK] {label} zip already downloaded.")
        return
    print(f"Downloading {label}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
        total_size = int(response.info().get('Content-Length', 0))
        block_size = 1024 * 1024  # 1MB
        block_num = 0
        while True:
            block = response.read(block_size)
            if not block:
                break
            out_file.write(block)
            block_num += 1
            print_progress(block_num, block_size, total_size)
    print(f"\n[OK] Downloaded {label} to {dest_path}")

def extract_zip(zip_path, extract_dir, label):
    # Check if we already extracted
    if os.path.exists(extract_dir) and len(os.listdir(extract_dir)) > 0:
        print(f"[OK] {label} already extracted.")
        return
    print(f"Extracting {label} zip file...")
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    print(f"[OK] Extracted {label} to {extract_dir}")

def find_jdk_home():
    for root, dirs, files in os.walk(JDK_EXTRACT_DIR):
        if "bin" in dirs and os.path.exists(os.path.join(root, "bin", "javac.exe")):
            return root
    raise FileNotFoundError("Could not find a valid JDK directory inside the extracted files.")

def find_gradle_bin():
    for root, dirs, files in os.walk(GRADLE_EXTRACT_DIR):
        if "bin" in dirs and os.path.exists(os.path.join(root, "bin", "gradle.bat")):
            return os.path.join(root, "bin", "gradle.bat")
    raise FileNotFoundError("Could not find gradleb.bat inside the extracted files.")

def main():
    print("=========================================")
    print(" LUNG-NET STANDALONE APK BUILD PIPELINE ")
    print("=========================================")

    # Ensure build environment folder exists
    os.makedirs(ENV_DIR, exist_ok=True)

    # 1. Download & Extract JDK 17
    try:
        download_file(JDK_URL, JDK_ZIP, "JDK 17")
        extract_zip(JDK_ZIP, JDK_EXTRACT_DIR, "JDK 17")
    except Exception as e:
        print(f"Error setting up JDK 17: {e}")
        sys.exit(1)

    # 2. Download & Extract Gradle 8.5
    try:
        download_file(GRADLE_URL, GRADLE_ZIP, "Gradle 8.5")
        extract_zip(GRADLE_ZIP, GRADLE_EXTRACT_DIR, "Gradle 8.5")
    except Exception as e:
        print(f"Error setting up Gradle 8.5: {e}")
        sys.exit(1)

    # 3. Find the JDK and Gradle executables
    try:
        jdk_home = find_jdk_home()
        gradle_bat = find_gradle_bin()
        print(f"JDK 17 Home: {jdk_home}")
        print(f"Gradle Command: {gradle_bat}")
    except Exception as e:
        print(f"Error finding tools: {e}")
        sys.exit(1)

    # 4. Generate local.properties for Android SDK
    local_props_path = os.path.join(WRAPPER_DIR, "local.properties")
    sdk_escaped = ANDROID_SDK_DIR.replace("\\", "\\\\").replace(":", "\\:")
    with open(local_props_path, "w") as f:
        f.write(f"sdk.dir={sdk_escaped}\n")
    print(f"[OK] Created local.properties specifying SDK path.")

    # 5. Compile Android App
    print("Compiling APK... This might take a few minutes for dependency resolution.")
    
    # Setup temporary environment variables for build process
    env = os.environ.copy()
    env["JAVA_HOME"] = jdk_home
    env["ANDROID_HOME"] = ANDROID_SDK_DIR
    
    # Append JDK bin and Gradle bin to PATH
    jdk_bin = os.path.join(jdk_home, "bin")
    gradle_bin = os.path.dirname(gradle_bat)
    env["PATH"] = f"{jdk_bin};{gradle_bin};{env.get('PATH', '')}"

    try:
        # Run Gradle command inside wrapper directory to build optimized debug APK
        result = subprocess.run(
            [gradle_bat, "assembleDebug"],
            cwd=WRAPPER_DIR,
            env=env,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Output gradle compile log to helper script log in case of errors
        log_path = os.path.join(WRAPPER_DIR, "build.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)

        if result.returncode != 0:
            print("[-] Compilation failed! Gradle output log written to android-wrapper/build.log")
            print("--- GRADLE ERROR OUTPUT PREVIEW ---")
            print("\n".join(result.stdout.splitlines()[-25:]))
            sys.exit(1)
        else:
            print("[OK] Compilation succeeded!")
    except Exception as e:
        print(f"Error executing build command: {e}")
        sys.exit(1)

    # 6. Copy final APK to root workspace directory
    apk_src = os.path.join(WRAPPER_DIR, "app", "build", "outputs", "apk", "debug", "app-debug.apk")
    apk_dest = os.path.join(BASE_DIR, "LUNG-NET.apk")
    
    if os.path.exists(apk_src):
        shutil.copyfile(apk_src, apk_dest)
        apk_size_mb = os.path.getsize(apk_dest) / (1024 * 1024)
        print("=========================================")
        print(" BUILD COMPLETE ")
        print(f"Standalone APK generated successfully: {apk_dest}")
        print(f"Final APK Size: {apk_size_mb:.2f} MB")
        print("=========================================")
    else:
        print(f"[-] Compiled APK not found in expected folder: {apk_src}")
        sys.exit(1)

if __name__ == "__main__":
    main()
