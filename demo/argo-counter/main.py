import time


def main():
    for i in range(1, 5):
        print(f"Count: {i}", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
