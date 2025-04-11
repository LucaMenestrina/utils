import logging
import warnings
import requests
class logger():
    def __init__(self, name="log", path=".", filemode="a", format="%(asctime)s - %(levelname)s \t %(message)s", console_level="INFO", file_level="INFO", telegram_level="INFO"):
        self.__levels = {"NOTSET":0, "DEBUG":10, "INFO":20, "WARNING":30, "ERROR":40, "CRITICAL":50}
        self.__name = name
        self.__path = path
        self.__format = format
        self.__formatter = logging.Formatter(self.__format)
        self.__filemode = filemode
        self.__console_level = console_level
        self.__file_level = file_level
        self.__telegram_level = telegram_level
        self.__logger = logging.getLogger(name)
        if self.__console_level:
            self.__createHandler("console", self.__formatter, self.__console_level)
        if self.__file_level:
            self.__createHandler("file", self.__formatter, self.__file_level)
        if self.__telegram_level:
            self.__createHandler("telegram", self.__formatter, self.__telegram_level)
        self.setLevel()
    def __createHandler(self, destination, formatter, level):
        if destination == "console":
            handler = logging.StreamHandler()
            handler.setFormatter(self.__formatter)
            handler.setLevel(level)
            self.__logger.addHandler(handler)
        elif destination == "file":
            handler = logging.FileHandler(filename = self.__name+".log", mode = self.__filemode)
            handler.setFormatter(self.__formatter)
            handler.setLevel(level)
            self.__logger.addHandler(handler)
        elif destination == "telegram":
            import dotenv
            dotenv.load_dotenv(override=True)
            import os
            self.__telegram_bot_id = os.getenv("telegram_bot_id")
            if not self.__telegram_bot_id:
                try:
                    self.__telegram_bot_id = input("No env variable 'telegram_bot_id', input it manually")#"1248830346:AAEFEReJ_BlO28Rtc_g9ra4wl3bsUs5ij6g"
                except:
                    warnings.warn("No Telegram Bot ID (Token)\nTelegramHandler will not be added")
                if self.__telegram_bot_id == "":
                    warnings.warn("No Telegram Bot ID (Token)\nTelegramHandler will not be added")
                    self.__telegram_bot_id = None
                    # print("TelegramHandler will not be added")
            self.__telegram_chat_id = os.getenv("telegram_chat_id")
            if not self.__telegram_chat_id:
                try:
                    self.__telegram_chat_id = input("No env variable 'telegram_chat_id', input it manually")#"858281897"
                except:
                    warnings.warn("No Telegram Chat ID\nTelegramHandler will not be added")
                if self.__telegram_chat_id == "":
                    warnings.warn("No Telegram Chat ID\nTelegramHandler will not be added")
                    self.__telegram_chat_id = None
                    # print("TelegramHandler will not be added")
            if self.__telegram_bot_id and self.__telegram_chat_id:
                self.__telegram_url = "https://api.telegram.org/bot"+self.__telegram_bot_id+"/sendMessage?chat_id="+self.__telegram_chat_id+"&parse_mode=Markdown&text="
                url = self.__telegram_url
                class TelegramHandler(logging.Handler):
                    def emit(self, message):
                        message = self.format(message)#.split("-")[-1][1:]#da cambiare
                        return requests.get(url+message)
                handler = TelegramHandler()
                handler.setFormatter(self.__formatter)
                handler.setLevel(level)
                self.__logger.addHandler(handler)
        else:
            raise ValueError("Handler type '%s' not implemented"%type)
    def __call__(self, message, level="info"):
        if level.upper() not in self.__levels:
            raise ValueError("Level '%s' not implemented"%level)
        getattr(self.__logger,level)(self.__checkmessage(message))
    def setName(self, name):
        self.__name = name
    def getName(self):
        return self.__name
    def getFile(self):
        if self.__file:
            return self.__name+".log"
        else:
            print("The logger is not saving to a file")
    def setLevel(self, level="DEBUG"):
        level = level.upper()
        if level not in self.__levels:
            raise ValueError("Level '%s' not implemented"%level)
        self.__logger.setLevel(getattr(logging,level))
    def getLevel(self):
        level = self.__logger.getEffectiveLevel()
        print(list(self.__levels.keys())[list(self.__levels.values()).index(level)])
    def __checkmessage(self,message):
        if message == "":
            warnings.warn("Your message is empty")
        else:
            return message
    def setFileMode(self, mode):
        if mode not in ["a","w"]:
            raise ValueError("File mode '%s' not implemented"%mode)
        self.__filemode = mode
    def getFileMode(self):
        return self.__filemode
    def setFormat(self, format):
        self.__formatter = logging.Formatter(format)
    def getFormat(self):
        return self.__format
    def setDateFormat(self, datefmt):
        pass
    def getDateFormat(self):
        pass

# log = logger("logger")
# log("ciao","info")
# log("", "")
# log("", "warning")
# log("ciao2")
# log.getLevel()
# log.getName()
# log.getFile()
# log.getFileMode()

# set datefmt
# path
# filters?
# format e level dovrebbero essere handler specific...
# da cambiare formato telegram
# nascondere token e id telegram
# inserire nome logger
