from posttroll.subscriber import Subscribe
import tomputils.util as tutil

def main():
    nameserver = tutil.get_env_var('NAMESERVER')
    topic = "pytroll://AVO/viirs/granule"
    with Subscribe('', topic, True, nameserver=nameserver) as sub:
        for msg in sub.recv():
            try:
                print(msg)
            except Exception as e:
                print("Exception: {}".format(e))


if __name__ == '__main__':
    main()
