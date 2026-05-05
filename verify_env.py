import sys
import importlib
import subprocess
import platform
import os
from pathlib import Path

def print_status(message, success):
    if success:
        print(f"\033[92m[✓]\033[0m {message}")
    else:
        print(f"\033[91m[✗]\033[0m {message}")

def main():
    os_name = platform.system()
    # Enable ANSI colors for Windows terminal
    if os_name == 'Windows':
        os.system('color')
        
    print("\n--- MedSight AI Environment Verification ---\n")
    all_passed = True
    issues = []

    # 1. Check Python Version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if py_version == "3.10.13":
        print_status(f"Python Version: {py_version}", True)
    else:
        print_status(f"Python Version: {py_version} (Expected 3.10.13)", False)
        all_passed = False
        issues.append("Install exact Python 3.10.13 via Conda.")

    # 2. Check PyTorch & CUDA
    try:
        import torch
        if torch.__version__.startswith("2.2.0"):
            print_status(f"PyTorch Version: {torch.__version__}", True)
        else:
            print_status(f"PyTorch Version: {torch.__version__} (Expected 2.2.0)", False)
            all_passed = False
            issues.append("Reinstall PyTorch 2.2.0 for CUDA 11.8.")

        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print_status(f"CUDA Available: YES ({torch.cuda.get_device_name(0)} - {vram_gb:.1f}GB VRAM)", True)
        else:
            print_status("CUDA Available: NO", False)
            all_passed = False
            issues.append("CUDA is not accessible. Check NVIDIA drivers and PyTorch CUDA build.")
    except ImportError:
        print_status("PyTorch not installed", False)
        all_passed = False
        issues.append("Install PyTorch.")

    # 3. Check Transformers
    try:
        import transformers
        if transformers.__version__ == "4.38.2":
            print_status(f"Transformers Version: {transformers.__version__}", True)
        else:
            print_status(f"Transformers Version: {transformers.__version__} (Expected 4.38.2)", False)
            all_passed = False
            issues.append("Install exact transformers version from requirements.txt.")
    except ImportError:
        print_status("Transformers not installed", False)
        all_passed = False

    # 4. Check Packages importable
    packages_to_test = ["fastapi", "sqlalchemy", "chromadb", "cv2", "PIL", "jose"]
    for pkg in packages_to_test:
        try:
            importlib.import_module(pkg)
        except ImportError:
            print_status(f"Package missing: {pkg}", False)
            all_passed = False
            issues.append(f"Install missing package: {pkg}")
            
    print_status("All key packages imported", len(issues) == 0 or all_passed)

    # 5. Check HF_HOME
    hf_home = os.getenv("HF_HOME")
    if hf_home:
        path = Path(hf_home)
        try:
            path.mkdir(parents=True, exist_ok=True)
            print_status(f"HF_HOME is set and writable ({hf_home})", True)
        except Exception:
            print_status(f"HF_HOME is set but NOT writable ({hf_home})", False)
            all_passed = False
            issues.append("Fix permissions for HF_HOME directory.")
    else:
        print_status("HF_HOME is NOT set", False)
        all_passed = False
        issues.append("Set HF_HOME environment variable permanently via PowerShell.")

    # 6. Test HuggingFace Download
    try:
        from huggingface_hub import hf_hub_download
        hf_hub_download(repo_id="lysandre/helloworld", filename="config.json")
        print_status("HuggingFace Hub download successful", True)
    except Exception as e:
        print_status("HuggingFace Hub download failed", False)
        all_passed = False
        issues.append(f"HuggingFace connection/download error: {e}")

    # 7. Check ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print_status("ffmpeg accessible in PATH", True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_status("ffmpeg NOT accessible in PATH", False)
        all_passed = False
        issues.append("Install ffmpeg and add to Windows PATH.")

    print("\n--------------------------------------------")
    if all_passed:
        print("\033[92m🟢 ALL SYSTEMS GO\033[0m\n")
    else:
        print("\033[91m🔴 FIX THESE ISSUES:\033[0m")
        for idx, issue in enumerate(issues, 1):
            print(f"  {idx}. {issue}")
        print()

if __name__ == "__main__":
    main()
