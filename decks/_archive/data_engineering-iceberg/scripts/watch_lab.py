import argparse
import time

from _lab_state import print_state


def main() -> None:
    parser = argparse.ArgumentParser(description="Iceberg 실습 상태 반복 관찰")
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()

    print("상태를 반복해서 읽습니다. 종료: Ctrl+C")
    try:
        while True:
            print("\033[2J\033[H", end="")
            print("ACTION   : 현재 실습 상태 읽기")
            print("CHANGE   : 없음")
            print_state()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n관찰을 종료했습니다.")


if __name__ == "__main__":
    main()
