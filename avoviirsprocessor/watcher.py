from posttroll.subscriber import Subscribe

def main():

    topic = "pytroll://AVO/viirs/granule"
    with Subscribe('', topic, True) as sub:
        for msg in sub.recv():
            try:
                print(msg)
            except Exception as e:
                print("Exception: {}".format(e))


if __name__ == '__main__':
    main()
