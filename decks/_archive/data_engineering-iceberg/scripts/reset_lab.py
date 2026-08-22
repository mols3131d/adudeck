import shutil

from _lab_state import warehouse_root


def main() -> None:
    root = warehouse_root()
    print(f"ACTION   : 실습 상태 초기화 ({root})")
    print("CHANGE   : SQLite Catalog와 warehouse 파일 제거")
    if root.exists():
        shutil.rmtree(root)
    print(f"VERIFY   : warehouse 디렉터리 없음 = {not root.exists()}")


if __name__ == "__main__":
    main()
