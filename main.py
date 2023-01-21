if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    from rielgobot_pro.entrypoint import main_loop

    main_loop()
