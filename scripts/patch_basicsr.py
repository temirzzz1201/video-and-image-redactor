from pathlib import Path
import basicsr


def main():
    basicsr_path = Path(basicsr.__file__).parent
    target = basicsr_path / "data" / "degradations.py"

    if not target.exists():
        print(f"ERROR: file not found: {target}")
        return 1

    text = target.read_text()

    old = "from torchvision.transforms.functional_tensor import rgb_to_grayscale"
    new = "from torchvision.transforms.functional import rgb_to_grayscale"

    if old in text:
        text = text.replace(old, new)
        target.write_text(text)
        print("BasicSR patched successfully")
        return 0

    if new in text:
        print("BasicSR is already patched")
        return 0

    print("WARNING: expected torchvision import was not found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
