from src.data import fetcher

def main():
    df = fetcher.get_history('sh600000', '20230101', '20231231', source='akshare', cache=True)
    print('empty=', df.empty)
    try:
        print('columns=', list(df.columns))
    except Exception as e:
        print('failed to list columns:', e)
    try:
        print(df.head())
    except Exception as e:
        print('failed to print head:', e)

if __name__ == '__main__':
    main()
